[app]

title = Micro Radar
package.name = microradar
package.domain = org.microradar
source.dir = ..
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = android/main.py,android/microradar_app/*,microradar_core/*
source.exclude_dirs = simulator,src,hardware,.git,.pio,.github,build,.vscode
source.main = android/main.py
version = 1.0.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,openssl,pyjnius,android

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 34
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]

log_level = 2
warn_on_root = 1
