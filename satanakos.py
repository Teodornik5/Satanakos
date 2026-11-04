import io
import os
import re
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image, ImageOps
from yt_dlp import YoutubeDL

# Η εφαρμογή όταν ανοίγει με διπλό κλικ δεν βλέπει τα προγράμματα του Homebrew.
# Γι' αυτό προσθέτουμε χειροκίνητα τους φακέλους τους.
os.environ["PATH"] += ":/opt/homebrew/bin:/usr/local/bin"

# Το ffmpeg είναι πακεταρισμένο μέσα στην εφαρμογή (πακέτο imageio_ffmpeg).
# Αν για κάποιο λόγο δεν βρεθεί, χρησιμοποιούμε αυτό που είναι εγκατεστημένο στο Mac.
try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"

# Για φωτογραφίες HEIC του iPhone (αν δεν υπάρχει, το προσπερνάμε)
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

# Λίστες με τις επεκτάσεις που ξέρουμε
VIDEO = [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".flv", ".wmv"]
AUDIO = [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"]
FOTO = [".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".bmp", ".heic", ".gif"]
RAW = [".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf"]  # φωτογραφίες RAW των μηχανών
KEIMENO = [".docx", ".doc", ".odt", ".rtf", ".txt", ".html"]

SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

# Το όνομα και η έκδοση της εφαρμογής (άλλαξε εδώ τον αριθμό σε κάθε νέα έκδοση)
ONOMA_EFARMOGIS = "Σατανάκος"
VERSION = "v1.1"

# ---------- Χρώματα (το πρώτο για φωτεινό θέμα, το δεύτερο για σκούρο) ----------
XROMA_FONTO = ("#F5F5F7", "#1C1C1E")        # φόντο παραθύρου
XROMA_KARTA = ("#FFFFFF", "#2C2C2E")        # λευκές "κάρτες"
XROMA_PEDIO = ("#F2F2F7", "#3A3A3C")        # φόντο πεδίων κειμένου
XROMA_KOUMPI2 = ("#E8E8ED", "#3A3A3C")      # δευτερεύοντα κουμπιά
XROMA_KOUMPI2_HOVER = ("#DCDCE1", "#48484A")
XROMA_KEIMENO = ("#1D1D1F", "#F5F5F7")
XROMA_DEFTERO = ("#86868B", "#98989D")      # γκρι κείμενο
XROMA_MPLE = "#007AFF"                      # το μπλε της Apple
XROMA_MPLE_HOVER = "#0A63D1"
XROMA_PRASINO = "#34C759"
XROMA_KOKKINO = "#FF3B30"

# Μήνυμα που φαίνεται κάτω κάτω στο παράθυρο
minima = "Έτοιμο."

# Μέγεθος του πλαισίου προεπισκόπησης (σε pixel). Ανανεώνεται μόνο του όταν
# αλλάζει το μέγεθος του παραθύρου ή όταν σύρεις τον διαχωριστή.
PW = 500
PH = 360
anamoni_megethous = None   # χρονόμετρο για να μην ξαναζωγραφίζεται η εικόνα σε κάθε pixel που σέρνεις
sirsimo = {"x": 0, "platos": 0}   # πού ξεκίνησε το σύρσιμο του διαχωριστή

# Μεταβλητές της προεπισκόπησης
lista_preview = []     # κάθε στοιχείο: (αριθμός ως κείμενο, αρχείο που θα φαίνεται)
thesi_preview = 0      # ποια φωτογραφία βλέπουμε τώρα
cache_eikonon = {}     # εικόνες που έχουν ήδη φορτωθεί, για να αλλάζουν γρήγορα
epilegmena_arxeia = []  # αρχεία που διάλεξες στη Μετατροπή και περιμένουν το "Προσθήκη"

# Ένα "κλειδί" για κάθε καρτέλα, ώστε να τρέχει μία δουλειά τη φορά
# (αλλιώς πολλά ffmpeg μαζί θα φορτώσουν πολύ το Mac)
kleidi_metatropis = threading.Lock()
kleidi_lipsis = threading.Lock()


# ---------- Μετατροπή και λήψη (ίδια με πριν) ----------

def diarkeia_arxeiou(arxeio):
    # Όταν δώσεις στο ffmpeg μόνο ένα αρχείο, γράφει μέσα στο κείμενό του τη διάρκεια
    # (μετά παραπονιέται ότι λείπει αρχείο εξόδου, αλλά αυτό δεν μας νοιάζει)
    apotelesma = subprocess.run([FFMPEG, "-i", arxeio], capture_output=True, text=True)
    eurema = re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", apotelesma.stderr)
    if eurema:
        return int(eurema.group(1)) * 3600 + int(eurema.group(2)) * 60 + float(eurema.group(3))
    return 0


def trekse_ffmpeg(ergasia, entoli, arxeio):
    # Τρέχει το ffmpeg και διαβάζει τι ώρα του βίντεο έχει φτάσει,
    # για να γεμίζει η μπάρα με το πραγματικό ποσοστό
    synolo = diarkeia_arxeiou(arxeio)
    diadikasia = subprocess.Popen(entoli, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True)
    ergasia["diadikasia"] = diadikasia   # την κρατάμε, για να μπορούμε να τη σταματήσουμε
    if ergasia["akirose"]:
        diadikasia.kill()   # η γραμμή σβήστηκε πριν προλάβει να ξεκινήσει
    teleftaio_sfalma = ""
    for grammi in diadikasia.stdout:
        grammi = grammi.strip()
        if grammi.startswith("out_time_ms="):
            try:
                deftera = int(grammi.split("=")[1]) / 1000000
                if synolo > 0:
                    ergasia["pososto"] = min(deftera / synolo, 0.99)
            except ValueError:
                pass
        elif " " in grammi:
            # οι γραμμές προόδου δεν έχουν κενά, τα μηνύματα σφάλματος έχουν
            teleftaio_sfalma = grammi
    diadikasia.wait()
    if diadikasia.returncode != 0:
        # Σβήνουμε το μισοτελειωμένο αρχείο (είναι το τελευταίο στοιχείο της εντολής),
        # αλλιώς μένει στον φάκελο ένα χαλασμένο αρχείο που δεν ανοίγει
        if os.path.exists(entoli[-1]):
            os.remove(entoli[-1])
        if ergasia["akirose"]:
            raise Exception("Ακυρώθηκε")
        raise Exception("Το ffmpeg απέτυχε: " + teleftaio_sfalma)


def metatropi(ergasia):
    arxeio = ergasia["arxeio"]
    nea = ergasia["morfi"]

    # Φτιάχνουμε το όνομα του νέου αρχείου (στον ίδιο φάκελο)
    onoma, katalixi = os.path.splitext(arxeio)
    katalixi = katalixi.lower()
    exodos = onoma + "." + nea
    if exodos == arxeio:
        exodos = onoma + "_νέο." + nea
    ergasia["exodos"] = exodos   # για να το σβήσουμε αν ακυρωθεί η γραμμή

    # --- ΒΙΝΤΕΟ και ΗΧΟΣ (με ffmpeg) ---
    if katalixi in VIDEO or katalixi in AUDIO:
        entoli = [FFMPEG, "-y", "-loglevel", "error", "-nostats",
                  "-progress", "pipe:1", "-i", arxeio]
        if "." + nea in AUDIO:
            entoli += ["-vn"]  # χωρίς εικόνα
            if nea == "mp3":
                entoli += ["-q:a", "0"]  # η καλύτερη ποιότητα mp3
            elif nea == "m4a" or nea == "aac":
                entoli += ["-c:a", "aac", "-b:a", "320k"]
        elif nea == "webm":
            entoli += ["-c:v", "libvpx-vp9", "-crf", "15", "-b:v", "0", "-c:a", "libopus"]
        else:
            # Δεν βάζουμε scale, άρα η ανάλυση μένει ίδια
            entoli += ["-c:v", "libx264", "-crf", "14", "-preset", "slow",
                       "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k"]
        entoli += [exodos]
        trekse_ffmpeg(ergasia, entoli, arxeio)

    # --- ΦΩΤΟΓΡΑΦΙΕΣ (με Pillow) ---
    elif katalixi in FOTO:
        eikona = Image.open(arxeio)
        if nea in ["jpg", "jpeg", "pdf"]:
            eikona = eikona.convert("RGB")  # το jpg δεν έχει διαφάνεια
        if nea in ["jpg", "jpeg"]:
            eikona.save(exodos, quality=100, subsampling=0)
        elif nea == "webp":
            eikona.save(exodos, lossless=True)
        else:
            eikona.save(exodos)

    # --- PDF -> WORD ---
    elif katalixi == ".pdf" and nea == "docx":
        # Το φορτώνουμε εδώ και όχι στην αρχή, ώστε η εφαρμογή να ανοίγει πάντα
        from pdf2docx import Converter
        c = Converter(arxeio)
        c.convert(exodos)
        c.close()

    # --- ΚΕΙΜΕΝΑ (με LibreOffice) ---
    elif katalixi in KEIMENO:
        # Τα κείμενα μετατρέπονται με το LibreOffice, που πρέπει να είναι εγκατεστημένο ξεχωριστά
        if not os.path.exists(SOFFICE):
            raise Exception("Για μετατροπή κειμένων χρειάζεται το LibreOffice. Κατέβασέ το από libreoffice.org")
        fakelos = os.path.dirname(arxeio)
        subprocess.run([SOFFICE, "--headless", "--convert-to", nea,
                        "--outdir", fakelos, arxeio], check=True)

    else:
        raise Exception("Δεν ξέρω αυτή τη μετατροπή: " + katalixi + " -> " + nea)


def lipsi(ergasia):
    sindesmos = ergasia["arxeio"]
    typos = ergasia["morfi"]

    # Το yt-dlp μας ειδοποιεί με αυτή τη συνάρτηση πόσο έχει κατέβει
    def pliroforia(d):
        if ergasia["akirose"]:
            raise Exception("Ακυρώθηκε")   # σταματάει τη λήψη
        # Θυμόμαστε ποια αρχεία γράφονται, για να τα σβήσουμε αν ακυρωθεί η λήψη
        for onoma_kleidiou in ["tmpfilename", "filename"]:
            if d.get(onoma_kleidiou):
                ergasia["arxeia_lipsis"].add(d[onoma_kleidiou])
        if d["status"] == "downloading":
            synolo = d.get("total_bytes") or d.get("total_bytes_estimate")
            if synolo:
                kommati = d["downloaded_bytes"] / synolo * 0.95
                # η μπάρα δεν γυρίζει ποτέ πίσω (το mp4 κατεβαίνει σε 2 κομμάτια)
                if kommati > ergasia["pososto"]:
                    ergasia["pososto"] = kommati
            titlos = d.get("info_dict", {}).get("title")
            if titlos:
                ergasia["onoma"] = titlos

    # Κατεβάζουμε στον φάκελο Downloads
    fakelos = os.path.expanduser("~/Downloads")
    epiloges = {"outtmpl": fakelos + "/%(title)s.%(ext)s",
                "progress_hooks": [pliroforia],
                "quiet": True, "no_warnings": True, "noprogress": True}
    if os.path.isfile(FFMPEG):
        epiloges["ffmpeg_location"] = FFMPEG  # το ffmpeg που είναι μέσα στην εφαρμογή
    if typos == "mp3":
        epiloges["format"] = "bestaudio/best"
        epiloges["postprocessors"] = [{"key": "FFmpegExtractAudio",
                                       "preferredcodec": "mp3",
                                       "preferredquality": "0"}]
    else:
        # Η καλύτερη εικόνα και ο καλύτερος ήχος, ενωμένα σε mp4
        epiloges["format"] = "bv*+ba/b"
        epiloges["merge_output_format"] = "mp4"
    with YoutubeDL(epiloges) as ydl:
        ydl.download([sindesmos])


def kathari_arxeia(ergasia):
    # Σβήνει τα αρχεία που έγραφε μια γραμμή που ακυρώθηκε
    arxeia = set(ergasia["arxeia_lipsis"])
    if ergasia["exodos"]:
        arxeia.add(ergasia["exodos"])
    for arxeio in arxeia:
        if os.path.exists(arxeio):
            os.remove(arxeio)


def trexe_ergasies(lista, kleidi, ti_na_kano):
    # Περνάει μία-μία τις δουλειές της λίστας (τρέχει στο παρασκήνιο)
    global minima
    for ergasia in lista:
        with kleidi:
            # Αν η γραμμή σβήστηκε όσο περίμενε, την προσπερνάμε
            if ergasia["akirose"] or ergasia["katastasi"] != "Αναμονή":
                continue
            ergasia["katastasi"] = "Σε εξέλιξη"
            try:
                ti_na_kano(ergasia)
                ergasia["pososto"] = 1
                ergasia["katastasi"] = "Τέλος"
            except Exception as e:
                if ergasia["akirose"]:
                    ergasia["katastasi"] = "Ακυρώθηκε"
                else:
                    ergasia["katastasi"] = "Σφάλμα"
                    minima = "Σφάλμα: " + str(e)[:200]
            # Αν η γραμμή σβήστηκε, σβήνουμε και ό,τι αρχείο μισογράφτηκε
            if ergasia["akirose"]:
                kathari_arxeia(ergasia)


# ---------- Επιλογή φωτογραφιών (ΝΕΟ) ----------

def kano_latinika(keimeno):
    # Τα ελληνικά κεφαλαία Τ, Η, Ν κλπ. μοιάζουν ακριβώς με τα λατινικά T, H, N
    # αλλά είναι άλλοι χαρακτήρες, και το όνομα του αρχείου δεν ταιριάζει.
    # Γι' αυτό τα αλλάζουμε σε λατινικά.
    antistoixia = {"Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K",
                   "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X"}
    for ellinika, latinika in antistoixia.items():
        keimeno = keimeno.replace(ellinika, latinika)
    return keimeno


def vres_arxeia(fakelos, prefix, katalixes):
    # Διαβάζει έναν φάκελο και φτιάχνει κατάλογο: αριθμός -> λίστα αρχείων
    # (π.χ. 913 -> ["THN00913.ARW"]). Συγκρίνουμε τους αριθμούς ως αριθμούς,
    # άρα το 913 και το 00913 είναι το ίδιο.
    katalogos = {}
    for onoma in os.listdir(fakelos):
        stem, katalixi = os.path.splitext(onoma)
        if katalixi.lower() in katalixes and stem.lower().startswith(prefix.lower()):
            ipoloipo = stem[len(prefix):]   # αυτό που μένει μετά το πρόθεμα
            if re.fullmatch(r"[0-9]+", ipoloipo):
                katalogos.setdefault(int(ipoloipo), []).append(onoma)
    return katalogos


def epilogi_fotografion(fakelos, prefix, katalixes, arithmoi, metakinisi, onoma_proorismou="selected"):
    # Τρέχει στο παρασκήνιο, για να μην κολλάει το παράθυρο όταν τα αρχεία είναι μεγάλα
    global minima
    try:
        neo_prefix = kano_latinika(prefix)
        allaxe_prefix = (neo_prefix != prefix)
        prefix = neo_prefix

        # Ο φάκελος προορισμού μπαίνει μέσα στον φάκελο που διάλεξες
        # (αν γράψεις ολόκληρη διαδρομή, π.χ. /Users/εσύ/Desktop/καλές, χρησιμοποιείται αυτή)
        selected = os.path.join(fakelos, os.path.expanduser(onoma_proorismou))
        if os.path.abspath(selected) == os.path.abspath(fakelos):
            raise Exception("Ο φάκελος προορισμού δεν μπορεί να είναι ο ίδιος με τον φάκελο των φωτογραφιών.")
        os.makedirs(selected, exist_ok=True)

        ola = vres_arxeia(fakelos, prefix, katalixes)         # τι υπάρχει στον φάκελο
        idi_mesa = vres_arxeia(selected, prefix, katalixes)   # τι υπάρχει ήδη στον φάκελο προορισμού

        vrethikan = 0
        ixane_idi = []
        den_vrethikan = []
        for grammi in arithmoi:
            # Κρατάμε μόνο τα ψηφία της γραμμής (αγνοεί κενά και αόρατους χαρακτήρες)
            psifia = re.sub(r"[^0-9]", "", grammi)
            if psifia == "":
                den_vrethikan.append(grammi)
                continue
            arithmos = int(psifia)
            if arithmos in ola:
                for onoma in ola[arithmos]:
                    apo = os.path.join(fakelos, onoma)
                    pros = os.path.join(selected, onoma)
                    if metakinisi:
                        shutil.move(apo, pros)
                    else:
                        shutil.copy2(apo, pros)  # κρατάει το αρχείο ακριβώς ίδιο
                    vrethikan += 1
                    minima = "Επεξεργασία... " + str(vrethikan) + " αρχεία"
            elif arithmos in idi_mesa:
                ixane_idi.append(psifia)
            else:
                den_vrethikan.append(psifia)

        minima = "Τέλος! Μεταφέρθηκαν " + str(vrethikan) + " αρχεία στον φάκελο " + onoma_proorismou + "."
        if allaxe_prefix:
            minima += " (Το πρόθεμα είχε ελληνικά γράμματα και τα άλλαξα σε λατινικά.)"
        if ixane_idi:
            minima += " Ήδη στον φάκελο " + onoma_proorismou + ": " + ", ".join(ixane_idi) + "."
        if den_vrethikan:
            minima += " Δεν βρέθηκαν: " + ", ".join(den_vrethikan)
        # Αν δεν βρέθηκε τίποτα, δείχνουμε ποια αρχεία υπάρχουν πραγματικά στον φάκελο
        if vrethikan == 0 and not ixane_idi:
            if ola:
                mikrotero = ola[min(ola)][0]
                megalitero = ola[max(ola)][0]
                minima += (" | Στον φάκελο υπάρχουν " + str(len(ola)) + " αρχεία " + ", ".join(katalixes)
                           + " με πρόθεμα " + prefix + ", από " + mikrotero + " έως " + megalitero + ".")
            else:
                minima += (" | Στον φάκελο δεν υπάρχει κανένα αρχείο με πρόθεμα " + prefix
                           + " και κατάληξη " + ", ".join(katalixes) + ".")
    except Exception as e:
        minima = "Σφάλμα: " + str(e)[:200]


def patise_epilogi():
    global minima
    fakelos = pedio_fakelou.get()
    if not os.path.isdir(fakelos):
        minima = "Διάλεξε πρώτα φάκελο."
        return
    # Διαβάζουμε τους αριθμούς: ένας ανά γραμμή, αγνοούμε τις κενές γραμμές
    arithmoi = []
    for grammi in kouti_arithmon.get("1.0", "end").split("\n"):
        if grammi.strip():
            arithmoi.append(grammi.strip())
    if not arithmoi:
        minima = "Γράψε τουλάχιστον έναν αριθμό."
        return
    prefix = pedio_prefix.get().strip()

    katalixes = diavase_katalixes()

    metakinisi = (switch_metakinisis.get() == 1)
    proorismos = pedio_proorismou.get().strip()
    if proorismos == "":
        proorismos = "selected"   # αν δεν γράψεις τίποτα, ο φάκελος λέγεται selected
    minima = "Ψάχνω τις φωτογραφίες..."
    threading.Thread(target=epilogi_fotografion,
                     args=(fakelos, prefix, katalixes, arithmoi, metakinisi, proorismos), daemon=True).start()


def epilogi_fakelou():
    fakelos = filedialog.askdirectory()
    if fakelos:
        pedio_fakelou.set(fakelos)
        fortose_preview()


# ---------- Προεπισκόπηση φωτογραφιών (ΝΕΟ) ----------

def diavase_katalixes():
    # Διαβάζουμε τις καταλήξεις: χωρισμένες με κόμμα, π.χ. "jpg, arw"
    katalixes = []
    for kommati in pedio_katalixis.get().split(","):
        kommati = kommati.strip().lower()
        if kommati:
            if not kommati.startswith("."):
                kommati = "." + kommati  # αν έγραψες "jpg" το κάνουμε ".jpg"
            katalixes.append(kommati)
    if not katalixes:
        katalixes = FOTO + RAW  # αν δεν γράψεις τίποτα, ψάχνει όλους τους τύπους φωτογραφιών
    return katalixes


def vres_prefix(fakelos, katalixes):
    # Βρίσκει το πρόθεμα που έχουν τα περισσότερα αρχεία (π.χ. "THN" από το THN00889.ARW)
    metrites = {}
    for onoma in os.listdir(fakelos):
        stem, katalixi = os.path.splitext(onoma)
        if katalixi.lower() in katalixes:
            m = re.fullmatch(r"(\D*)(\d+)", stem)
            if m:
                metrites[m.group(1)] = metrites.get(m.group(1), 0) + 1
    if not metrites:
        return ""
    return max(metrites, key=metrites.get)


def fortose_eikona(arxeio):
    # Ανοίγει μια φωτογραφία και τη μικραίνει για να χωράει στο πλαίσιο
    katalixi = os.path.splitext(arxeio)[1].lower()
    if katalixi in RAW:
        # Τα RAW δεν ανοίγουν κατευθείαν. Βγάζουμε τη μικρή JPEG που έχουν μέσα τους.
        import rawpy
        raw = rawpy.imread(arxeio)
        thumb = raw.extract_thumb()
        peristrofi = raw.sizes.flip   # πώς κρατούσες τη μηχανή (0 = κανονικά)
        raw.close()
        if thumb.format == rawpy.ThumbFormat.JPEG:
            eikona = Image.open(io.BytesIO(thumb.data))
        else:
            eikona = Image.fromarray(thumb.data)
        if eikona.getexif().get(274, 1) != 1:
            eikona = ImageOps.exif_transpose(eikona)   # η μικρή JPEG ξέρει την περιστροφή
        elif peristrofi == 3:
            eikona = eikona.rotate(180)
        elif peristrofi == 6:
            eikona = eikona.rotate(270, expand=True)
        elif peristrofi == 5:
            eikona = eikona.rotate(90, expand=True)
    else:
        eikona = Image.open(arxeio)
        eikona = ImageOps.exif_transpose(eikona)
    eikona = eikona.convert("RGB")
    eikona.thumbnail((2000, 2000))   # αρκετά μεγάλη ώστε να γεμίζει και μεγάλο πλαίσιο
    return eikona


def pare_eikona(arxeio):
    # Αν την έχουμε ήδη φορτώσει την παίρνουμε από την "κρύπτη" (cache), αλλιώς τη φορτώνουμε
    if arxeio not in cache_eikonon:
        cache_eikonon[arxeio] = fortose_eikona(arxeio)
        if len(cache_eikonon) > 8:
            cache_eikonon.pop(next(iter(cache_eikonon)))   # πετάμε την πιο παλιά
    return cache_eikonon[arxeio]


def kratimena_arithmoi():
    # Οι αριθμοί που υπάρχουν ήδη στο κουτί (ως ακέραιοι)
    arithmoi = set()
    for grammi in kouti_arithmon.get("1.0", "end").split("\n"):
        psifia = re.sub(r"[^0-9]", "", grammi)
        if psifia:
            arithmoi.add(int(psifia))
    return arithmoi


def fortose_preview():
    # Διαβάζει τον φάκελο και φτιάχνει τη λίστα των φωτογραφιών για την προεπισκόπηση
    global lista_preview, thesi_preview
    fakelos = pedio_fakelou.get()
    if not os.path.isdir(fakelos):
        return
    katalixes = diavase_katalixes()
    prefix = kano_latinika(pedio_prefix.get().strip())
    ola = vres_arxeia(fakelos, prefix, katalixes)
    if not ola:
        # Δεν ταίριαξε το πρόθεμα που έγραψες (ή είναι κενό): το βρίσκουμε μόνοι μας
        neo_prefix = vres_prefix(fakelos, katalixes)
        if neo_prefix != "" and neo_prefix != prefix:
            prefix = neo_prefix
            pedio_prefix.set(prefix)
            ola = vres_arxeia(fakelos, prefix, katalixes)

    lista_preview = []
    for arithmos in sorted(ola):
        # αν υπάρχουν RAW και JPG με τον ίδιο αριθμό, δείχνουμε το JPG (ανοίγει πιο γρήγορα)
        arxeia = sorted(ola[arithmos], key=lambda o: os.path.splitext(o)[1].lower() in RAW)
        stem = os.path.splitext(arxeia[0])[0]
        lista_preview.append((stem[len(prefix):], arxeia[0]))
    thesi_preview = 0
    cache_eikonon.clear()
    deikse_fotografia()


def deikse_fotografia():
    # Δείχνει τη φωτογραφία που βρίσκεται στη θέση thesi_preview
    global eikona_ctk
    if not lista_preview:
        eikona_label.configure(image=kenh_eikona, text="Δεν βρέθηκαν φωτογραφίες")
        onoma_preview.configure(text="")
        koumpi_kratisis.configure(text="Κράτα", fg_color=XROMA_MPLE, hover_color=XROMA_MPLE_HOVER)
        return
    arithmos_keimeno, onoma_arxeiou = lista_preview[thesi_preview]
    zografise_eikona()
    onoma_preview.configure(text=str(thesi_preview + 1) + " / " + str(len(lista_preview))
                            + "   ·   " + onoma_arxeiou)
    # Το κουμπί αλλάζει αν η φωτογραφία είναι ήδη στη λίστα
    if int(arithmos_keimeno) in kratimena_arithmoi():
        koumpi_kratisis.configure(text="Κρατήθηκε ✓  (πάτα για αφαίρεση)",
                                  fg_color=XROMA_PRASINO, hover_color="#2AA84A")
    else:
        koumpi_kratisis.configure(text="Κράτα αυτή τη φωτογραφία",
                                  fg_color=XROMA_MPLE, hover_color=XROMA_MPLE_HOVER)
    # Φορτώνουμε από πριν την επόμενη, για να αλλάζει αμέσως όταν πατήσεις →
    parathiro.after(50, prosfortose_epomeni)


def zografise_eikona():
    # Βάζει τη φωτογραφία στο πλαίσιο, στο μεγαλύτερο μέγεθος που χωράει (χωρίς να παραμορφώνεται)
    global eikona_ctk
    if not lista_preview:
        return
    onoma_arxeiou = lista_preview[thesi_preview][1]
    try:
        eikona = pare_eikona(os.path.join(pedio_fakelou.get(), onoma_arxeiou))
        klimaka = min(PW / eikona.width, PH / eikona.height)
        eikona_ctk = ctk.CTkImage(light_image=eikona, dark_image=eikona,
                                  size=(max(1, int(eikona.width * klimaka)),
                                        max(1, int(eikona.height * klimaka))))
        eikona_label.configure(image=eikona_ctk, text="")
    except Exception as e:
        eikona_label.configure(image=kenh_eikona, text="Δεν μπορώ να δείξω αυτό το αρχείο: " + str(e)[:120])


def allaxe_megethos_preview(event):
    # Τρέχει κάθε φορά που αλλάζει το μέγεθος του πλαισίου της προεπισκόπησης
    global PW, PH, anamoni_megethous
    PW = max(100, event.width - 24)
    PH = max(100, event.height - 24)
    if anamoni_megethous is not None:
        parathiro.after_cancel(anamoni_megethous)
    anamoni_megethous = parathiro.after(40, zografise_eikona)


def ksekina_sirsimo(event):
    # Πάτησες το ποντίκι πάνω στον διαχωριστή: θυμόμαστε πού ήταν
    sirsimo["x"] = event.x_root
    sirsimo["platos"] = deksia.winfo_width()


def sirsimo_diaxoristi(event):
    # Σέρνεις τον διαχωριστή: αν πας δεξιά στενεύει το δεξί μέρος, αν πας αριστερά φαρδαίνει
    diafora = event.x_root - sirsimo["x"]
    neo_platos = sirsimo["platos"] - diafora
    megisto = stiles.winfo_width() - 300   # να μένει πάντα χώρος για την προεπισκόπηση
    neo_platos = max(340, min(neo_platos, megisto))
    deksia.configure(width=neo_platos)


def diaxoristis_hover(mesa):
    # Η λεπτή γραμμή του διαχωριστή φαίνεται πιο έντονα όταν περνάς το ποντίκι από πάνω
    if mesa:
        grip.configure(fg_color=XROMA_DEFTERO)
    else:
        grip.configure(fg_color=XROMA_KOUMPI2)


def prosfortose_epomeni():
    if thesi_preview + 1 < len(lista_preview):
        try:
            pare_eikona(os.path.join(pedio_fakelou.get(), lista_preview[thesi_preview + 1][1]))
        except Exception:
            pass


def epomeni_fotografia():
    global thesi_preview
    parathiro.focus_set()   # να δουλεύουν τα βελάκια του πληκτρολογίου
    if thesi_preview < len(lista_preview) - 1:
        thesi_preview += 1
        deikse_fotografia()


def proigoumeni_fotografia():
    global thesi_preview
    parathiro.focus_set()
    if thesi_preview > 0:
        thesi_preview -= 1
        deikse_fotografia()


def kratise_fotografia():
    # Βάζει τον αριθμό της φωτογραφίας στη λίστα (ή τον βγάζει αν υπάρχει ήδη)
    parathiro.focus_set()
    if not lista_preview:
        return
    arithmos_keimeno = lista_preview[thesi_preview][0]
    if int(arithmos_keimeno) in kratimena_arithmoi():
        # Αφαίρεση: ξαναγράφουμε το κουτί χωρίς τη γραμμή αυτής της φωτογραφίας
        nees_grammes = []
        for grammi in kouti_arithmon.get("1.0", "end").split("\n"):
            psifia = re.sub(r"[^0-9]", "", grammi)
            if grammi.strip() and not (psifia and int(psifia) == int(arithmos_keimeno)):
                nees_grammes.append(grammi.strip())
        kouti_arithmon.delete("1.0", "end")
        if nees_grammes:
            kouti_arithmon.insert("1.0", "\n".join(nees_grammes) + "\n")
    else:
        keimeno = kouti_arithmon.get("1.0", "end-1c")
        if keimeno != "" and not keimeno.endswith("\n"):
            kouti_arithmon.insert("end-1c", "\n")
        kouti_arithmon.insert("end-1c", arithmos_keimeno + "\n")
        kouti_arithmon.see("end")
    deikse_fotografia()


def pliktro(event):
    # Συντομεύσεις: ← → αλλάζουν φωτογραφία, το κενό (Space) κρατάει/αφαιρεί
    if menu_panw.get() != "Επιλογή":
        return
    try:
        if isinstance(parathiro.focus_get(), (tk.Entry, tk.Text)):
            return   # αν πληκτρολογείς σε κουτάκι, δεν αλλάζουμε φωτογραφία
    except KeyError:
        return
    if event.keysym == "Right":
        epomeni_fotografia()
    elif event.keysym == "Left":
        proigoumeni_fotografia()
    elif event.keysym == "space":
        kratise_fotografia()


# ---------- Λίστες εργασιών ----------

def kontino(onoma):
    # Κόβει τα πολύ μεγάλα ονόματα για να χωράνε στη λίστα
    if len(onoma) > 38:
        return onoma[:35] + "..."
    return onoma


def prosthese_ergasia(kartela, onoma, morfi, arxeio):
    # Φτιάχνει μια νέα γραμμή στη λίστα της καρτέλας
    plaisio = kartela["plaisio"]
    kartela["metritis"] += 1
    seira = kartela["metritis"]

    # Πρώτα φτιάχνουμε τα δεδομένα της γραμμής, μετά τα κουμπιά και τα κείμενα
    ergasia = {"onoma": onoma, "morfi": morfi, "arxeio": arxeio,
               "pososto": 0, "katastasi": "Αναμονή", "emfanizetai": None,
               "akirose": False,       # γίνεται True όταν πατήσεις το ✕
               "diadikasia": None,     # το ffmpeg που τρέχει για αυτή τη γραμμή
               "exodos": None,         # το αρχείο που φτιάχνεται
               "arxeia_lipsis": set()}  # τα αρχεία που γράφει το yt-dlp

    e_onoma = ctk.CTkLabel(plaisio, text=kontino(onoma), anchor="w",
                           font=gramma(13), text_color=XROMA_KEIMENO)
    e_onoma.grid(row=seira, column=0, sticky="ew", padx=10, pady=6)
    e_morfi = ctk.CTkLabel(plaisio, text=morfi.upper(), width=56, height=24,
                           corner_radius=8, fg_color=XROMA_KOUMPI2,
                           font=gramma(11, "bold"), text_color=XROMA_KEIMENO)
    e_morfi.grid(row=seira, column=1, padx=10, pady=6)
    bara = ctk.CTkProgressBar(plaisio, width=190, height=6, corner_radius=3,
                              fg_color=XROMA_PEDIO, progress_color=XROMA_MPLE)
    bara.set(0)
    bara.grid(row=seira, column=2, padx=10, pady=6)
    e_katastasi = ctk.CTkLabel(plaisio, text="Αναμονή", width=90,
                               font=gramma(12), text_color=XROMA_DEFTERO)
    e_katastasi.grid(row=seira, column=3, padx=10, pady=6)
    # Το κουμπί ✕ που σβήνει τη γραμμή (και σταματάει τη δουλειά αν τρέχει)
    e_svisimo = ctk.CTkButton(plaisio, text="✕", width=28, height=28, corner_radius=14,
                              fg_color="transparent", text_color=XROMA_DEFTERO,
                              hover_color=("#FFD9D6", "#5A2C2A"), font=gramma(13),
                              command=lambda: afairese_ergasia(kartela, ergasia))
    e_svisimo.grid(row=seira, column=4, padx=(0, 10), pady=6)

    ergasia["e_onoma"] = e_onoma
    ergasia["e_morfi"] = e_morfi
    ergasia["bara"] = bara
    ergasia["e_katastasi"] = e_katastasi
    ergasia["e_svisimo"] = e_svisimo
    kartela["lista"].append(ergasia)
    return ergasia


def sviste_grammi(kartela, ergasia):
    # Σβήνει τα κουμπιά και τα κείμενα της γραμμής και τη βγάζει από τη λίστα
    for onoma_widget in ["e_onoma", "e_morfi", "bara", "e_katastasi", "e_svisimo"]:
        ergasia[onoma_widget].destroy()
    kartela["lista"].remove(ergasia)


def afairese_ergasia(kartela, ergasia):
    # Το κουμπί ✕: βγάζει τη γραμμή από τη λίστα, ακόμα κι αν τρέχει τώρα ή περιμένει
    global minima
    ergasia["akirose"] = True
    diadikasia = ergasia["diadikasia"]
    if diadikasia is not None and diadikasia.poll() is None:
        diadikasia.kill()   # σταματάει το ffmpeg αμέσως
    minima = "Αφαιρέθηκε: " + ergasia["onoma"]
    sviste_grammi(kartela, ergasia)


def katharismos(kartela):
    # Σβήνει από τη λίστα όσες δουλειές τελείωσαν ή έδωσαν σφάλμα
    for ergasia in list(kartela["lista"]):
        if ergasia["katastasi"] in ["Τέλος", "Σφάλμα"]:
            sviste_grammi(kartela, ergasia)


def ananeosi():
    # Κάθε 0.2 δευτερόλεπτα ανανεώνει τις μπάρες και τα κείμενα της λίστας
    for kartela in [kartela_arxeion, kartela_lipsis]:
        for ergasia in kartela["lista"]:
            timi = (ergasia["onoma"], ergasia["pososto"], ergasia["katastasi"])
            if timi == ergasia["emfanizetai"]:
                continue  # δεν άλλαξε τίποτα, δεν ξαναζωγραφίζουμε
            ergasia["emfanizetai"] = timi

            ergasia["e_onoma"].configure(text=kontino(ergasia["onoma"]))
            ergasia["bara"].set(ergasia["pososto"])
            if ergasia["katastasi"] == "Σε εξέλιξη":
                keimeno = str(int(ergasia["pososto"] * 100)) + "%"
            else:
                keimeno = ergasia["katastasi"]
            ergasia["e_katastasi"].configure(text=keimeno)

            # Πράσινο όταν τελειώσει, κόκκινο όταν υπάρχει σφάλμα
            if ergasia["katastasi"] == "Τέλος":
                ergasia["bara"].configure(progress_color=XROMA_PRASINO)
                ergasia["e_katastasi"].configure(text_color=XROMA_PRASINO)
            elif ergasia["katastasi"] == "Σφάλμα":
                ergasia["bara"].configure(progress_color=XROMA_KOKKINO)
                ergasia["e_katastasi"].configure(text_color=XROMA_KOKKINO)
    etiketa_minimatos.configure(text=minima)
    parathiro.after(200, ananeosi)


def epilogi_arxeion():
    # Διαλέγεις αρχεία, αλλά ΔΕΝ μπαίνουν στη λίστα μέχρι να πατήσεις "Προσθήκη"
    global epilegmena_arxeia
    arxeia = filedialog.askopenfilenames()
    if arxeia:
        epilegmena_arxeia = list(arxeia)
        if len(arxeia) == 1:
            pedio_epilegmenon.set("1 αρχείο")
        else:
            pedio_epilegmenon.set(str(len(arxeia)) + " αρχεία")


def patise_prosthiki():
    # Βάζει τα επιλεγμένα αρχεία στη λίστα με τη μορφή που έχει επιλεγεί τώρα
    # και η μετατροπή τους ξεκινάει αμέσως
    global epilegmena_arxeia, minima
    if not epilegmena_arxeia:
        minima = "Διάλεξε πρώτα αρχεία."
        return
    nea_lista = []
    for arxeio in epilegmena_arxeia:
        nea_lista.append(prosthese_ergasia(kartela_arxeion, os.path.basename(arxeio),
                                           menu_typou.get(), arxeio))
    minima = "Προστέθηκαν " + str(len(nea_lista)) + " αρχεία."
    epilegmena_arxeia = []
    pedio_epilegmenon.set("Κανένα αρχείο")
    threading.Thread(target=trexe_ergasies,
                     args=(nea_lista, kleidi_metatropis, metatropi), daemon=True).start()


def patise_lipsi(event=None):
    global minima
    sindesmos = pedio_link.get().strip()
    if "spotify" in sindesmos:
        minima = "Το Spotify έχει DRM (κλείδωμα), δεν γίνεται λήψη."
        return
    if not sindesmos:
        minima = "Βάλε πρώτα σύνδεσμο."
        return
    ergasia = prosthese_ergasia(kartela_lipsis, sindesmos, menu_lipsis.get(), sindesmos)
    pedio_link.set("")
    threading.Thread(target=trexe_ergasies,
                     args=([ergasia], kleidi_lipsis, lipsi), daemon=True).start()


# ---------- Μικρές συναρτήσεις για το στυλ (ώστε όλα να μοιάζουν ίδια) ----------

def gramma(megethos=13, varos="normal"):
    # Η γραμματοσειρά του συστήματος του Mac (SF)
    return ctk.CTkFont(family=".AppleSystemUIFont", size=megethos, weight=varos)


def koumpi_kirio(parent, keimeno, entoli, platos=140):
    # Το μπλε κουμπί της Apple
    return ctk.CTkButton(parent, text=keimeno, command=entoli, width=platos, height=34,
                         corner_radius=10, fg_color=XROMA_MPLE, hover_color=XROMA_MPLE_HOVER,
                         text_color="white", font=gramma(13, "bold"))


def koumpi_deftero(parent, keimeno, entoli, platos=140):
    # Το γκρι κουμπί
    return ctk.CTkButton(parent, text=keimeno, command=entoli, width=platos, height=34,
                         corner_radius=10, fg_color=XROMA_KOUMPI2, hover_color=XROMA_KOUMPI2_HOVER,
                         text_color=XROMA_KEIMENO, font=gramma(13))


def menu_epilogis(parent, timi_lista, platos=90):
    return ctk.CTkOptionMenu(parent, values=timi_lista, width=platos, height=34, corner_radius=10,
                             fg_color=XROMA_KOUMPI2, button_color=XROMA_KOUMPI2,
                             button_hover_color=XROMA_KOUMPI2_HOVER, text_color=XROMA_KEIMENO,
                             dropdown_fg_color=XROMA_KARTA, dropdown_text_color=XROMA_KEIMENO,
                             dropdown_hover_color=XROMA_PEDIO, font=gramma(13),
                             dropdown_font=gramma(13))


def pedio_keimenou(parent, **kwargs):
    return ctk.CTkEntry(parent, height=34, corner_radius=10, border_width=0,
                        fg_color=XROMA_PEDIO, text_color=XROMA_KEIMENO,
                        placeholder_text_color=XROMA_DEFTERO, font=gramma(13), **kwargs)


def karta(parent):
    # Λευκό πλαίσιο με στρογγυλεμένες γωνίες
    return ctk.CTkFrame(parent, fg_color=XROMA_KARTA, corner_radius=16)


def ftiaxe_lista(parent):
    # Φτιάχνει τη λίστα (με κύλιση) και την πρώτη γραμμή με τους τίτλους
    plaisio = ctk.CTkScrollableFrame(parent, fg_color=XROMA_KARTA, corner_radius=16)
    plaisio.pack(fill="both", expand=True, pady=(10, 0))
    plaisio.grid_columnconfigure(0, weight=1)
    titloi = ["ΟΝΟΜΑ", "ΜΟΡΦΗ", "ΠΡΟΟΔΟΣ", "ΚΑΤΑΣΤΑΣΗ", ""]
    for i in range(5):
        ctk.CTkLabel(plaisio, text=titloi[i], anchor="w", font=gramma(11, "bold"),
                     text_color=XROMA_DEFTERO).grid(row=0, column=i, sticky="w", padx=10, pady=(6, 4))
    return {"plaisio": plaisio, "lista": [], "metritis": 0}


def allagi_selidas(onoma):
    # Δείχνει μόνο τη σελίδα που επέλεξες από το πάνω μενού
    for selida in selides.values():
        selida.pack_forget()
    selides[onoma].pack(fill="both", expand=True, padx=20, pady=(0, 5))


# ---------- Το παράθυρο ----------
ctk.set_appearance_mode("system")   # ακολουθεί το φωτεινό/σκούρο θέμα του Mac

parathiro = ctk.CTk(fg_color=XROMA_FONTO)
parathiro.title(ONOMA_EFARMOGIS)
parathiro.geometry("1120x740")
parathiro.minsize(1000, 680)

pedio_link = ctk.StringVar()
pedio_fakelou = ctk.StringVar(value="Δεν έχεις διαλέξει φάκελο")
pedio_prefix = ctk.StringVar()
pedio_katalixis = ctk.StringVar()
pedio_proorismou = ctk.StringVar()
pedio_epilegmenon = ctk.StringVar(value="Κανένα αρχείο")

# Το μενού πάνω πάνω, όπως τα κουμπιά επιλογής της Apple
menu_panw = ctk.CTkSegmentedButton(
    parathiro, values=["Μετατροπή", "Λήψη", "Επιλογή"], command=allagi_selidas,
    height=32, corner_radius=9, font=gramma(13),
    selected_color=("#FFFFFF", "#636366"), selected_hover_color=("#FFFFFF", "#636366"),
    unselected_color=("#E3E3E8", "#2C2C2E"), unselected_hover_color=("#D8D8DD", "#3A3A3C"),
    text_color=XROMA_KEIMENO)
menu_panw.pack(pady=(18, 14))

etiketa_minimatos = ctk.CTkLabel(parathiro, text=minima, wraplength=1040,
                                 font=gramma(12), text_color=XROMA_DEFTERO)
etiketa_minimatos.pack(side="bottom", pady=(0, 12))

# Η έκδοση κάτω δεξιά, με μικρά γράμματα
etiketa_version = ctk.CTkLabel(parathiro, text=VERSION, font=gramma(10), text_color=XROMA_DEFTERO)
etiketa_version.place(relx=1.0, rely=1.0, x=-14, y=-8, anchor="se")

selida1 = ctk.CTkFrame(parathiro, fg_color="transparent")
selida2 = ctk.CTkFrame(parathiro, fg_color="transparent")
selida3 = ctk.CTkFrame(parathiro, fg_color="transparent")
selides = {"Μετατροπή": selida1, "Λήψη": selida2, "Επιλογή": selida3}

# --- Σελίδα 1: Μετατροπή αρχείων ---
karta1 = karta(selida1)
karta1.pack(fill="x")
koumpi_deftero(karta1, "Επιλογή αρχείων...", epilogi_arxeion, 160).pack(side="left", padx=(16, 8), pady=14)
ctk.CTkLabel(karta1, textvariable=pedio_epilegmenon, width=90, anchor="w", font=gramma(12),
             text_color=XROMA_DEFTERO).pack(side="left", padx=(0, 8))
ctk.CTkLabel(karta1, text="Μετατροπή σε", font=gramma(13),
             text_color=XROMA_DEFTERO).pack(side="left", padx=(8, 8))
menu_typou = menu_epilogis(karta1, ["mp4", "mov", "mkv", "webm", "mp3", "wav", "flac", "m4a",
                                    "jpg", "png", "webp", "tiff", "pdf", "docx", "txt"])
menu_typou.pack(side="left")
koumpi_kirio(karta1, "Προσθήκη", patise_prosthiki, 110).pack(side="right", padx=16)

kouti1 = ctk.CTkFrame(selida1, fg_color="transparent")
kouti1.pack(side="bottom", fill="x", pady=(8, 0))
kartela_arxeion = ftiaxe_lista(selida1)
koumpi_deftero(kouti1, "Καθαρισμός ολοκληρωμένων",
               lambda: katharismos(kartela_arxeion), 200).pack(side="left")

# --- Σελίδα 2: Λήψη από σύνδεσμο ---
karta2 = karta(selida2)
karta2.pack(fill="x")
entry_link = pedio_keimenou(karta2, textvariable=pedio_link,
                            placeholder_text="Βάλε σύνδεσμο YouTube ή Instagram")
entry_link.pack(side="left", fill="x", expand=True, padx=(16, 8), pady=14)
entry_link.bind("<Return>", patise_lipsi)  # το Enter ξεκινάει τη λήψη
menu_lipsis = menu_epilogis(karta2, ["mp4", "mp3"], 80)
menu_lipsis.pack(side="left", padx=8)
koumpi_kirio(karta2, "Λήψη", patise_lipsi, 100).pack(side="left", padx=(8, 16))

kouti2 = ctk.CTkFrame(selida2, fg_color="transparent")
kouti2.pack(side="bottom", fill="x", pady=(8, 0))
kartela_lipsis = ftiaxe_lista(selida2)
koumpi_deftero(kouti2, "Καθαρισμός ολοκληρωμένων",
               lambda: katharismos(kartela_lipsis), 200).pack(side="left")

# --- Σελίδα 3: Επιλογή φωτογραφιών ---
karta3 = karta(selida3)
karta3.pack(fill="both", expand=True)

# Πάνω: ο φάκελος
grammi_fakelou = ctk.CTkFrame(karta3, fg_color="transparent")
grammi_fakelou.pack(fill="x", padx=16, pady=(16, 8))
koumpi_deftero(grammi_fakelou, "Επιλογή φακέλου...", epilogi_fakelou, 160).pack(side="left")
koumpi_deftero(grammi_fakelou, "Ανανέωση", fortose_preview, 100).pack(side="right")
ctk.CTkLabel(grammi_fakelou, textvariable=pedio_fakelou, anchor="w", wraplength=520,
             font=gramma(12), text_color=XROMA_DEFTERO).pack(side="left", padx=12)

# Κάτω: τρεις στήλες. Αριστερά η προεπισκόπηση (παίρνει όλο τον χώρο που περισσεύει),
# στη μέση ο διαχωριστής που σέρνεται, δεξιά τα πεδία (στενή στήλη).
stiles = ctk.CTkFrame(karta3, fg_color="transparent")
stiles.pack(fill="both", expand=True, padx=16, pady=(0, 14))
stiles.grid_rowconfigure(0, weight=1)
stiles.grid_columnconfigure(0, weight=1)

aristera = ctk.CTkFrame(stiles, fg_color="transparent")
aristera.grid(row=0, column=0, sticky="nsew")
diaxoristis = ctk.CTkFrame(stiles, fg_color="transparent", width=18)
diaxoristis.grid(row=0, column=1, sticky="ns")
deksia = ctk.CTkFrame(stiles, fg_color="transparent", width=360)
deksia.grid(row=0, column=2, sticky="ns")
deksia.pack_propagate(False)   # το πλάτος το ορίζει ο διαχωριστής, όχι τα στοιχεία μέσα

# --- Διαχωριστής: διάφανη μπάρα με μια λεπτή γραμμή στη μέση ---
grip = ctk.CTkFrame(diaxoristis, width=4, height=56, corner_radius=2, fg_color=XROMA_KOUMPI2)
grip.place(relx=0.5, rely=0.5, anchor="center")
for stoixeio in [diaxoristis, grip]:
    stoixeio.bind("<Button-1>", ksekina_sirsimo)
    stoixeio.bind("<B1-Motion>", sirsimo_diaxoristi)
    stoixeio.bind("<Enter>", lambda event: diaxoristis_hover(True))
    stoixeio.bind("<Leave>", lambda event: diaxoristis_hover(False))
    try:
        tk.Frame.configure(stoixeio, cursor="sb_h_double_arrow")   # βελάκι ↔ πάνω από τον διαχωριστή
    except Exception:
        pass

# --- Αριστερά: προεπισκόπηση ---
kenh_eikona = ctk.CTkImage(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), size=(1, 1))
# Πρώτα βάζουμε κάτω κάτω τα κουμπιά και το όνομα, μετά το πλαίσιο της εικόνας παίρνει ό,τι περισσεύει
ctk.CTkLabel(aristera, text="← → αλλαγή φωτογραφίας  ·  Space = κράτημα", font=gramma(11),
             text_color=XROMA_DEFTERO).pack(side="bottom", pady=(8, 0))
koumpia_preview = ctk.CTkFrame(aristera, fg_color="transparent")
koumpia_preview.pack(side="bottom", fill="x")
koumpi_deftero(koumpia_preview, "◀", proigoumeni_fotografia, 56).pack(side="left")
koumpi_deftero(koumpia_preview, "▶", epomeni_fotografia, 56).pack(side="right")
koumpi_kratisis = koumpi_kirio(koumpia_preview, "Κράτα", kratise_fotografia, 200)
koumpi_kratisis.pack(side="left", fill="x", expand=True, padx=8)
onoma_preview = ctk.CTkLabel(aristera, text="", font=gramma(12), text_color=XROMA_DEFTERO)
onoma_preview.pack(side="bottom", pady=(8, 6))

kadro_preview = ctk.CTkFrame(aristera, fg_color=XROMA_PEDIO, corner_radius=12)
kadro_preview.pack(fill="both", expand=True)
eikona_label = ctk.CTkLabel(kadro_preview, text="Διάλεξε φάκελο για προεπισκόπηση", image=kenh_eikona,
                            fg_color="transparent", text_color=XROMA_DEFTERO, font=gramma(13))
eikona_label.place(relx=0.5, rely=0.5, anchor="center")   # στο κέντρο, χωρίς να επηρεάζει το μέγεθος του πλαισίου
kadro_preview.bind("<Configure>", allaxe_megethos_preview)

# --- Δεξιά: πρόθεμα, κατάληξη, φάκελος προορισμού, αριθμοί ---
grammi_onomatos = ctk.CTkFrame(deksia, fg_color="transparent")
grammi_onomatos.pack(fill="x")

stili_prefix = ctk.CTkFrame(grammi_onomatos, fg_color="transparent")
stili_prefix.pack(side="left", fill="x", expand=True, padx=(0, 6))
ctk.CTkLabel(stili_prefix, text="Πρόθεμα (π.χ. IMG_)", anchor="w",
             font=gramma(12, "bold"), text_color=XROMA_DEFTERO).pack(fill="x", padx=2, pady=(0, 4))
entry_prefix = pedio_keimenou(stili_prefix, textvariable=pedio_prefix, placeholder_text="IMG_")
entry_prefix.pack(fill="x")
entry_prefix.bind("<Return>", lambda event: fortose_preview())

stili_katalixis = ctk.CTkFrame(grammi_onomatos, fg_color="transparent")
stili_katalixis.pack(side="left", fill="x", expand=True, padx=(6, 0))
ctk.CTkLabel(stili_katalixis, text="Κατάληξη (κενό = όλες)", anchor="w",
             font=gramma(12, "bold"), text_color=XROMA_DEFTERO).pack(fill="x", padx=2, pady=(0, 4))
entry_katalixis = pedio_keimenou(stili_katalixis, textvariable=pedio_katalixis, placeholder_text="jpg, arw")
entry_katalixis.pack(fill="x")
entry_katalixis.bind("<Return>", lambda event: fortose_preview())

ctk.CTkLabel(deksia, text="Φάκελος προορισμού (κενό = selected)", anchor="w",
             font=gramma(12, "bold"), text_color=XROMA_DEFTERO).pack(fill="x", padx=2, pady=(12, 4))
pedio_keimenou(deksia, textvariable=pedio_proorismou, placeholder_text="selected").pack(fill="x")

ctk.CTkLabel(deksia, text="Αριθμοί φωτογραφιών (ένας ανά γραμμή)", anchor="w",
             font=gramma(12, "bold"), text_color=XROMA_DEFTERO).pack(fill="x", padx=2, pady=(12, 4))
katw_grammi = ctk.CTkFrame(deksia, fg_color="transparent")
katw_grammi.pack(side="bottom", fill="x", pady=(10, 0))
kouti_arithmon = ctk.CTkTextbox(deksia, corner_radius=10, fg_color=XROMA_PEDIO,
                                text_color=XROMA_KEIMENO, font=gramma(13))
kouti_arithmon.pack(fill="both", expand=True)

# Στη στενή στήλη ο διακόπτης και το κουμπί μπαίνουν το ένα κάτω από το άλλο
switch_metakinisis = ctk.CTkSwitch(katw_grammi, text="Μετακίνηση αντί για αντιγραφή",
                                   progress_color=XROMA_MPLE, font=gramma(13),
                                   text_color=XROMA_KEIMENO)
switch_metakinisis.pack(anchor="w", padx=2)
koumpi_kirio(katw_grammi, "Επιλογή φωτογραφιών", patise_epilogi, 180).pack(fill="x", pady=(10, 0))

# Τα βελάκια και το Space δουλεύουν σε όλο το παράθυρο
parathiro.bind("<Key>", pliktro)

# Ξεκινάμε από την πρώτη σελίδα
menu_panw.set("Μετατροπή")
allagi_selidas("Μετατροπή")

ananeosi()
parathiro.mainloop()
