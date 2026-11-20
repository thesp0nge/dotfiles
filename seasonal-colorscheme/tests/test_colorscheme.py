import contextlib
import datetime as dt
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SOURCE))
import colorscheme as cs
import install
import render

class CalendarTests(unittest.TestCase):
    def test_all_months_and_leap_day(self):
        expected=("winter","winter","spring","spring","spring","summer",
                  "summer","summer","autumn","autumn","autumn","winter")
        for month,season in enumerate(expected,1):
            self.assertEqual(cs.season_for_date(dt.date(2026,month,1)),season)
        self.assertEqual(cs.season_for_date(dt.date(2028,2,29)),"winter")

    def test_boundaries(self):
        for before,after,old,new in [
            ("2026-02-28","2026-03-01","winter","spring"),
            ("2026-05-31","2026-06-01","spring","summer"),
            ("2026-08-31","2026-09-01","summer","autumn"),
            ("2026-11-30","2026-12-01","autumn","winter")]:
            self.assertEqual(cs.season_for_date(dt.date.fromisoformat(before)),old)
            self.assertEqual(cs.season_for_date(dt.date.fromisoformat(after)),new)

    def test_manual_survives_a_calendar_boundary(self):
        mode={"mode":"manual","season":"summer"}
        self.assertEqual(cs.selected_season(mode,dt.date(2026,12,1)),"summer")
        self.assertEqual(cs.selected_season({"mode":"auto"},dt.date(2026,12,1)),
                         "winter")

class RenderTests(unittest.TestCase):
    def test_profiles_parse_and_keep_palette(self):
        palettes=json.loads((SOURCE/"palettes.json").read_text())
        for name,p in palettes.items():
            files=render.render(p)
            self.assertEqual(tomllib.loads(files["alacritty.toml"])
                             ["colors"]["primary"]["background"],p["background"])
            self.assertEqual(tomllib.loads(files["starship.toml"])
                             ["palettes"]["seasonal"]["accent"],p["accent"])
            compile(files["ranger.py"],name,"exec")
            for value in p.values():
                if value.startswith("#"):
                    self.assertTrue(16<=render.nearest(value)<=255)

    def test_toml_roundtrip_preserves_noncolor_settings(self):
        data={"format":"$directory$character","add_newline":False,
              "directory":{"style":"bold accent","truncation_length":3},
              "general":{"import":["one.toml","two.toml"]},
              "keyboard":{"bindings":[{"key":"N","mods":"Control","action":"SpawnNewInstance"}]}}
        self.assertEqual(tomllib.loads(render.dump_toml(data)),data)

class MigrationTests(unittest.TestCase):
    def test_install_switch_and_restore(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.ExitStack() as stack:
            home=Path(temp)
            config=home/".config"
            state=home/".local/state/colorscheme"
            for key,value in (("HOME",home),("CONFIG",config),
                              ("ROOT",config/"colorscheme"),("STATE",state)):
                stack.enter_context(patch.object(cs,key,value))
            stack.enter_context(patch.object(os,"geteuid",return_value=1000))
            stack.enter_context(patch.dict(os.environ,{
                "HOME":str(home),"ZDOTDIR":str(home),
                "XDG_CONFIG_HOME":str(config),"STARSHIP_CONFIG":str(config/"starship.toml")}))
            stack.enter_context(patch.object(cs.shutil,"which",return_value=None))
            before={
                ".zshrc":"# my shell\nalias x='echo x'\n",
                ".tmux.conf":"set -g prefix C-a\nset -g status-style 'fg=#e89446,bg=#211b17'\n",
                ".config/ranger/rc.conf":"set show_hidden true\n",
                ".config/alacritty/alacritty.toml":
                    '[window]\nstartup_mode="Fullscreen"\n[colors.primary]\nbackground="#211b17"\n',
                ".config/starship.toml":
                    'palette="autumn"\nformat="$directory"\n[palettes.autumn]\naccent="#e89446"\n',
            }
            for relative,text in before.items():
                cs.atomic(home/relative,text)
            with contextlib.redirect_stdout(io.StringIO()):
                backup=install.install(no_systemd=True)
            for season in cs.SEASONS:
                with contextlib.redirect_stdout(io.StringIO()):
                    cs.set_mode(season)
                self.assertEqual((cs.ROOT/"current").resolve().name,season)
                self.assertIn("prefix C-a",(home/".tmux.conf").read_text())
                self.assertIn("alias x=",(home/".zshrc").read_text())
                self.assertIn("show_hidden true",(config/"ranger/rc.conf").read_text())
                self.assertEqual(tomllib.loads((config/"alacritty/alacritty.toml")
                                 .read_text())["window"]["startup_mode"],"Fullscreen")
                active=tomllib.loads((config/"starship.toml").read_text())
                p=json.loads((cs.ROOT/season/"palette.json").read_text())
                self.assertEqual(active["palettes"]["seasonal"]["accent"],p["accent"])
            with contextlib.redirect_stdout(io.StringIO()):
                cs.set_mode("auto")
                cs.restore(backup)
            for relative,text in before.items():
                self.assertEqual((home/relative).read_text(),text)
            self.assertFalse(cs.ROOT.exists())
            self.assertFalse((home/".local/bin/colorscheme").exists())

    def test_bad_toml_changes_nothing(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.ExitStack() as stack:
            home=Path(temp)
            for key,value in (("HOME",home),("CONFIG",home/".config"),
                              ("ROOT",home/".config/colorscheme")):
                stack.enter_context(patch.object(cs,key,value))
            stack.enter_context(patch.object(os,"geteuid",return_value=1000))
            stack.enter_context(patch.dict(os.environ,{
                "ZDOTDIR":str(home),"XDG_CONFIG_HOME":str(home/".config"),
                "STARSHIP_CONFIG":str(home/".config/starship.toml")}))
            cs.atomic(home/".config/alacritty/alacritty.toml","[invalid")
            with self.assertRaises(tomllib.TOMLDecodeError):
                install.preflight()
            self.assertFalse(cs.ROOT.exists())

if __name__=="__main__":
    unittest.main()

# Invocation is unittest discovery; no host services or desktop state are touched.
