import os
import glob
import json
import re
import shutil
from pprint import pprint

current_dir = os.path.dirname(os.path.realpath(__file__))
base_path = os.path.join(current_dir, "../repos")
search_pattern = f'repos/**/src/**/devcontainer-feature.json'

def feature_to_env(name):
  name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).upper()

def feature_to_opam_option(name):
  return feature_to_env(name).lower().replace('_', '-')

def filter_versions(vs):
  return [v for v in vs if v not in ['os-provided', 'none']]

def get_submodule_url(repo_path, submodule_path):
  import configparser
  import os

  gitmodules_path = os.path.join(repo_path, ".gitmodules")
    
  if not os.path.exists(gitmodules_path):
    raise Exception(f"No .gitmodules file found at {repo_path}")
    
  config = configparser.ConfigParser()
  config.read(gitmodules_path)

  for section in config.sections():
    path = config.get(section, "path")
    if path == submodule_path:
      return config.get(section, "url")
    
  raise Exception(f"No submodule found at {submodule_path}")

def option_to_opam_env(lang, option):
  env = feature_to_env(option)
  pkg = feature_to_opam_option(option)
  s = "\"{env}=%{{dev-{lang}-{pkg}:version}}%\" {{dev-{lang}-{pkg}:installed}}"
  return s.format(lang=lang, env=env, pkg=pkg)

def create_opam_file(lang, args):
  options = args['options']
  options_v = options.get('version',{})
  versions = filter_versions(options_v.get('proposals', options_v.get('enum',[])))
  description = args.get('description', f"The {lang} devcontainer image")
  homepage = args.get('documentationURL', "https://devcontainers.io")

  options = {k: v for k, v in options.items() if k != 'version'}
  for option,val in options.items():
    option_name = feature_to_opam_option(option)
    synopsis = val.get('description', "")
    template = """
opam-version: "2.0"
synopsis: "{synopsis}"
description: "Installing this package selects the `{version}` {option} option for dev-{lang}."
homepage: "{homepage}"
depends: [ ]
"""
    if val['type'] == 'string':
      vs = val.get('proposals',val.get('enum',[]));
      if vs == []:
        vs = [val.get('default')]
      if vs == [""]:
        vs = []
      for version in vs:
        pkg_dir = f"packages/dev-{lang}-{option_name}/dev-{lang}-{option_name}.{version}/"
        opam_option = template.format(homepage=homepage, synopsis=synopsis, lang=lang, option=option, version=version)
        os.makedirs(pkg_dir, exist_ok=True)
        with open(f"{pkg_dir}/opam", "w") as f: 
          f.write(opam_option)
    elif val['type'] == 'boolean':
      version = "1"
      pkg_dir = f"packages/dev-{lang}-{option_name}/dev-{lang}-{option_name}.{version}/"
      opam_option = template.format(homepage=homepage, synopsis=synopsis, lang=lang, option=option, version=version)
      os.makedirs(pkg_dir, exist_ok=True)
      with open(f"{pkg_dir}/opam", "w") as f: 
        f.write(opam_option)

  option_entries=list(map(lambda o: option_to_opam_env(lang, o), options.keys()))
  if len(option_entries) > 0:
    option_vars = "\n  ".join(option_entries)
  else:
    option_vars = "# no options for this package"
  option_depopts = " ".join(list(map(lambda o : "\"dev-"+lang+"-"+feature_to_opam_option(o)+'"', options.keys())))
  synopsis = args.get('name', f"The {lang} devcontainer")
  template = """
opam-version: "2.0"
synopsis: "{synopsis}"
description: "{description}"
homepage: "{homepage}"
depends: [ ]
install: [
  "env"
  "VERSION=%{{version}}%"
  {option_vars}
  "bash" "./src/{lang}/install.sh"
]
depopts: [ {option_depopts} ]
url {{ src: "git+{repo_url}" }}
"""
  opam_file_content = template.format(synopsis=synopsis, homepage=homepage,description=description,option_vars=option_vars, option_depopts=option_depopts, lang=lang, repo_url=args['repo_url'])
  for version in versions:
    dir_path = f"packages/dev-{lang}/dev-{lang}.{version}"
    os.makedirs(dir_path, exist_ok=True)
    with open(f"{dir_path}/opam", "w") as f:
      f.write(opam_file_content)

langs={}
for filename in glob.glob(search_pattern, recursive=True):
  with open(filename, 'r') as file:
    data = json.load(file)
    dirs = filename.split(os.path.sep)
    lang = dirs[dirs.index('src')+1]
    repo = dirs[dirs.index('src')-1]
    repo_url = get_submodule_url('.', "repos/"+repo)
    data['repo_url'] = repo_url
    data.setdefault('options',{})
    langs[lang] = data

shutil.rmtree('packages')
for key,value in langs.items():
  create_opam_file(key, value)
