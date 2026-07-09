[app]

title = Micro Radar
package.name = microradar
package.domain = org.microradar
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = main.py,microradar_app/*,microradar_core/*
source.exclude_dirs = data,.buildozer,bin
source.main = main.py
version = 1.1.0

requirements = python3==3.11.8,hostpython3==3.11.8,kivy==2.3.0,kivymd==1.2.0,requests,openssl,pyjnius,android,cython==0.29.36

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 34
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
android.cython_version = 0.29.36
p4a.branch = v2024.01.21

[buildozer]

log_level = 2
warn_on_root = 1
