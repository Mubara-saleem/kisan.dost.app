# Smart Kisan (سمارٹ کسان)

Urdu-first advisory app for cotton farmers in Pakistan. Final year project.

## Features (phase 1)
- Urdu right-to-left UI with large text and icons
- District and sowing-date setup (saved on the device)
- 7-day weather forecast with a rain alert (Open-Meteo, no API key)
- Crop calendar that follows the sowing date
- Mandi rates screen (empty until you add real rates)
- Voice button that reads advice aloud (needs an Urdu text-to-speech voice on the phone)
- Pest/disease detection: placeholder screen (phase 2)

## Important: content must be verified
The crop calendar text in `lib/data/calendar_stages.dart` is generic placeholder
content. Replace it with recommendations from CCRI Multan, PCCC or your provincial
agriculture department before real farmers use the app. Do not add spray or
fertilizer doses without an official source. Mandi rates are intentionally empty.

## Run it
1. Install Flutter: https://docs.flutter.dev/get-started/install
2. In this folder, generate the platform folders (keeps `lib/` and `pubspec.yaml`):
   ```
   flutter create . --project-name smart_kisan --platforms android
   ```
3. Install packages and run:
   ```
   flutter pub get
   flutter run
   ```
4. For release builds, add this line inside `<manifest>` in
   `android/app/src/main/AndroidManifest.xml` (internet for weather):
   ```xml
   <uses-permission android:name="android.permission.INTERNET"/>
   ```
   For voice on Android 11+, also add inside `<manifest>`:
   ```xml
   <queries>
     <intent><action android:name="android.intent.action.TTS_SERVICE"/></intent>
   </queries>
   ```

## Project structure
```
lib/
  main.dart                 app entry, Urdu locale
  theme.dart                colors and large Urdu text
  data/                     districts, crop stages, mandi rates
  services/                 weather API, saved settings
  screens/                  welcome, home, weather, calendar, mandi, pest
  widgets/speak_button.dart text-to-speech button
```

## Push to GitHub
```
git init
git add .
git commit -m "Initial commit: Smart Kisan starter app"
git branch -M main
git remote add origin https://github.com/<your-username>/smart-kisan.git
git push -u origin main
```
(Create the empty repository on github.com first, without a README.)

## Roadmap
- [ ] Verify and complete crop calendar content with official sources
- [ ] Real mandi rates (admin panel / Firebase)
- [ ] Reminder notifications for calendar stages
- [ ] Pest/disease detection with TensorFlow Lite
- [ ] Offline caching of the last forecast
- [ ] Test with 15 to 20 farmers (SUS questionnaire)
