#!/bin/bash
# Εγκαθιστά ό,τι χρειάζεται και φτιάχνει την εφαρμογή Σατανάκος.app
# Τρέξ' το από τον φάκελο όπου βρίσκεται το satanakos.py

# Η έκδοση διαβάζεται από το satanakos.py (π.χ. "v1.0" -> "1.0"), ώστε να την αλλάζεις σε ένα μόνο σημείο
EKDOSI=$(grep '^VERSION' satanakos.py | cut -d'"' -f2)
EKDOSI=${EKDOSI#v}

# Το rawpy διαβάζει τη μικρή JPEG μέσα στα RAW αρχεία (.arw) για την προεπισκόπηση
pip3 install customtkinter pyinstaller pillow pillow-heif yt-dlp pdf2docx imageio-ffmpeg rawpy

# Εσωτερικά η εφαρμογή λέγεται Satanakos (λατινικά, για να μην δημιουργηθούν προβλήματα)
pyinstaller --windowed --noconfirm --name "Satanakos" \
  --icon icon.icns \
  --collect-all customtkinter \
  --collect-all pillow_heif \
  --collect-all pdf2docx \
  --collect-all pymupdf \
  --collect-all yt_dlp \
  --collect-all imageio_ffmpeg \
  --collect-all rawpy \
  satanakos.py

# Βάζουμε το ελληνικό όνομα και την έκδοση στο αρχείο πληροφοριών της εφαρμογής
# (έτσι φαίνονται στο Dock και στο πάνω μενού του Mac)
PLIST="dist/Satanakos.app/Contents/Info.plist"
orise() {
  /usr/libexec/PlistBuddy -c "Set :$1 $2" "$PLIST" 2>/dev/null || /usr/libexec/PlistBuddy -c "Add :$1 string $2" "$PLIST"
}
orise CFBundleName "Σατανάκος"
orise CFBundleDisplayName "Σατανάκος"
orise CFBundleShortVersionString "$EKDOSI"
orise CFBundleVersion "$EKDOSI"

# Μετονομάζουμε την εφαρμογή σε Σατανάκος.app
rm -rf "dist/Σατανάκος.app"
mv "dist/Satanakos.app" "dist/Σατανάκος.app"

# Υπογραφή "στο χέρι" (ad-hoc): τα Mac με Apple Silicon σκοτώνουν προγράμματα χωρίς υπογραφή,
# και το ffmpeg που μπήκε μέσα στην εφαρμογή είναι ένα τέτοιο πρόγραμμα
codesign --force --deep --sign - "dist/Σατανάκος.app"

# Zip για διανομή: ο φίλος σου το ξεζιπάρει και σέρνει την εφαρμογή στα Applications
ditto -c -k --keepParent "dist/Σατανάκος.app" "dist/Satanakos-v$EKDOSI.zip"

echo "Έτοιμο! Έκδοση $EKDOSI:"
echo "  Εφαρμογή: dist/Σατανάκος.app"
echo "  Zip:      dist/Satanakos-v$EKDOSI.zip"
