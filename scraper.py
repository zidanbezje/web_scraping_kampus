from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from dotenv import load_dotenv
import os
import re
import time

BASE_URL = "https://elearning.ubpkarawang.ac.id"
PROFILE_NAME_CACHE = {}


def start_driver():
    options = Options()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    return driver, wait



def login(driver, wait):
    load_dotenv()
    username = os.getenv("MOODLE_USERNAME")
    password = os.getenv("MOODLE_PASSWORD")

    if not username or not password:
        raise Exception("Username atau password tidak terbaca dari .env")

    driver.get(f"{BASE_URL}/login/index.php")

    wait.until(EC.presence_of_element_located((By.ID, "username")))
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "loginbtn").click()

    wait.until(EC.url_contains("/my/"))



def get_tahun_list(driver, wait):
    driver.get("https://elearning.ubpkarawang.ac.id/course")
    wait.until(EC.presence_of_element_located((By.ID, "page-content")))

    elements = driver.find_elements(By.XPATH, "//a[contains(@href,'categoryid=')]")

    data = []
    for el in elements:
        nama = el.text.strip()
        url = el.get_attribute("href")

        # filter valid
        if nama and "tahun akademik" in nama.lower():
            data.append({
                "nama": nama,
                "url": url
            })

    # ======================
    # HAPUS DUPLIKAT
    # ======================
    unique = {}
    for item in data:
        unique[item["nama"]] = item

    return list(unique.values())

def get_prodi_list(driver, wait, tahun_url):
    driver.get(tahun_url)
    wait.until(EC.presence_of_element_located((By.ID, "page-content")))

    elements = driver.find_elements(
        By.XPATH, "//a[contains(@href,'categoryid=')]"
    )

    data = []

    for el in elements:
        nama = el.text.strip()
        url = el.get_attribute("href")

        # ======================
        # FILTER VALID
        # ======================
        if (
            nama
            and "semester" not in nama.lower()
            and "tahun akademik" not in nama.lower()
            and "perkuliahan" not in nama.lower()
        ):
            data.append({
                "nama": nama,
                "url": url
            })

    # ======================
    # HAPUS DUPLIKAT
    # ======================
    unique = {}
    for item in data:
        unique[item["nama"]] = item

    prodi_list = list(unique.values())

    # ======================
    # SORT (OPSIONAL BIAR RAPI)
    # ======================
    prodi_list.sort(key=lambda x: x["nama"])

    return prodi_list


def normalize_space(text):
    return re.sub(r"\s+", " ", (text or "")).strip()



def clean_dosen_name(text):
    text = normalize_space(text)
    if not text:
        return ""

    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s*Dosen\s*$", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s*Teacher\s*$", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^Course Contacts:\s*", "", text, flags=re.IGNORECASE).strip()
    return text



def dedupe_keep_order(items):
    result = []
    seen = set()

    for item in items:
        key = normalize_space(item).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(normalize_space(item))

    return result



def get_profile_name(driver, wait, profile_url):
    if not profile_url:
        return ""

    if profile_url in PROFILE_NAME_CACHE:
        return PROFILE_NAME_CACHE[profile_url]

    current_url = driver.current_url

    try:
        driver.get(profile_url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".page-header-headings h1, h1")))

        name_el = driver.find_element(By.CSS_SELECTOR, ".page-header-headings h1, h1")
        name = clean_dosen_name(name_el.text)
        PROFILE_NAME_CACHE[profile_url] = name
        return name
    except Exception:
        PROFILE_NAME_CACHE[profile_url] = ""
        return ""
    finally:
        try:
            driver.get(current_url)
            wait.until(EC.presence_of_element_located((By.ID, "page-content")))
            time.sleep(1)
        except Exception:
            pass



def extract_dosen_names_from_contact_elements(driver, wait, contact_elements):
    names = []

    for contact in contact_elements:
        try:
            candidates = [
                contact.get_attribute("title"),
                contact.get_attribute("data-original-title"),
                contact.get_attribute("aria-label"),
                contact.text,
            ]

            img_elements = contact.find_elements(By.CSS_SELECTOR, "img")
            for img in img_elements:
                candidates.append(img.get_attribute("alt"))
                candidates.append(img.get_attribute("title"))

            found_name = ""
            for candidate in candidates:
                cleaned = clean_dosen_name(candidate)
                if cleaned and cleaned.lower() not in {"dosen", "teacher"}:
                    found_name = cleaned
                    break

            if not found_name:
                href = contact.get_attribute("href")
                found_name = get_profile_name(driver, wait, href)

            if found_name:
                names.append(found_name)
        except StaleElementReferenceException:
            continue
        except Exception:
            continue

    return dedupe_keep_order(names)



def extract_dosen_names_from_course_card(driver, wait, card):
    contact_selectors = [
        "a.course-contact",
        ".course-contacts a",
        ".card-footer a[href*='/user/profile.php']",
    ]

    for selector in contact_selectors:
        contact_elements = card.find_elements(By.CSS_SELECTOR, selector)
        if contact_elements:
            names = extract_dosen_names_from_contact_elements(driver, wait, contact_elements)
            if names:
                return names

    img_elements = card.find_elements(By.CSS_SELECTOR, "img[alt]")
    names = []
    for img in img_elements:
        alt_text = clean_dosen_name(img.get_attribute("alt"))
        if alt_text and alt_text.lower() not in {"dosen", "teacher"}:
            names.append(alt_text)

    return dedupe_keep_order(names)



def extract_course_name_and_url_from_card(card):
    link_selectors = [
        ".course-info-container .coursename a[href*='/course/view.php?id=']",
        ".course-info-container a.aalink[href*='/course/view.php?id=']",
        ".card-body .coursename a[href*='/course/view.php?id=']",
        ".card-body a.aalink[href*='/course/view.php?id=']",
        "a.aalink[href*='/course/view.php?id=']",
        "a[href*='/course/view.php?id=']",
    ]

    for selector in link_selectors:
        for link in card.find_elements(By.CSS_SELECTOR, selector):
            text_candidates = [
                link.text,
                link.get_attribute("title"),
                link.get_attribute("aria-label"),
            ]

            parent_text = ""
            try:
                parent = link.find_element(By.XPATH, "ancestor::*[contains(@class,'coursename')][1]")
                parent_text = parent.text
            except Exception:
                pass

            if parent_text:
                text_candidates.insert(0, parent_text)

            course_name = ""
            for candidate in text_candidates:
                cleaned = normalize_space(candidate)
                if cleaned:
                    course_name = cleaned
                    break

            course_url = link.get_attribute("href")

            if course_url and course_name:
                return course_name, course_url

    return "", ""



def extract_courses_from_semester_page(driver, wait):
    courses = []

    # Prioritas: layout card dashboard Moodle
    card_elements = driver.find_elements(By.CSS_SELECTOR, "div.card.dashboard-card")
    if card_elements:
        for card in card_elements:
            try:
                course_name, course_url = extract_course_name_and_url_from_card(card)

                if not course_name or not course_url or "pkkmb" in course_name.lower():
                    continue

                dosen_names = extract_dosen_names_from_course_card(driver, wait, card)

                courses.append({
                    "nama": course_name,
                    "url": course_url,
                    "dosen": ", ".join(dosen_names) if dosen_names else "Tidak ditemukan",
                })
            except NoSuchElementException:
                continue
            except StaleElementReferenceException:
                continue

        if courses:
            return courses

    # Fallback lama: ambil semua link course, lalu cari dosen belakangan
    course_elements = driver.find_elements(By.XPATH, "//a[contains(@href,'/course/view.php?id=')]")
    seen_urls = set()

    for el in course_elements:
        try:
            nama = normalize_space(el.text)
            url = el.get_attribute("href")

            if not nama or not url or "pkkmb" in nama.lower() or url in seen_urls:
                continue

            seen_urls.add(url)
            courses.append({
                "nama": nama,
                "url": url,
                "dosen": "Tidak ditemukan",
            })
        except StaleElementReferenceException:
            continue

    return courses



def extract_dosen_names_from_course_page(driver, wait):
    selectors = [
        "a.course-contact",
        ".course-contacts a[href*='/user/profile.php']",
        "img[alt*='Dosen']",
        "img[alt*='Teacher']",
    ]

    names = []

    for selector in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        if not elements:
            continue

        if selector.startswith("img"):
            for img in elements:
                alt_text = clean_dosen_name(img.get_attribute("alt"))
                if alt_text:
                    names.append(alt_text)
        else:
            names.extend(extract_dosen_names_from_contact_elements(driver, wait, elements))

    return dedupe_keep_order(names)



def scrape(tahun_obj, prodi_obj, driver, wait):
    results = []

    try:
        # ======================
        # MASUK HALAMAN COURSE
        # ======================
        driver.get(f"{BASE_URL}/course")
        wait.until(EC.presence_of_element_located((By.ID, "page-content")))

        # ======================
        # MASUK TAHUN
        # ======================
        driver.get(tahun_obj["url"])
        wait.until(EC.presence_of_element_located((By.ID, "page-content")))
        time.sleep(2)

        # ======================
        # MASUK PRODI
        # ======================
        driver.get(prodi_obj["url"])
        wait.until(EC.presence_of_element_located((By.ID, "page-content")))
        time.sleep(2)

        # ======================
        # SEMESTER
        # ======================
        semester_elements = driver.find_elements(
            By.XPATH, "//a[contains(@href,'categoryid=')]"
        )

        semester_data = []
        for el in semester_elements:
            nama = normalize_space(el.text)
            url = el.get_attribute("href")

            if "semester" in nama.lower():
                semester_data.append({
                    "nama": nama,
                    "url": url
                })

        # ======================
        # LOOP SEMESTER
        # ======================
        for semester in semester_data:
            driver.get(semester["url"])
            wait.until(EC.presence_of_element_located((By.ID, "page-content")))
            time.sleep(2)

            # ======================
            # AMBIL COURSE
            # ======================
            courses = extract_courses_from_semester_page(driver, wait)
            print(f"\n[{semester['nama']}] total course:", len(courses))

            for course in courses:
                driver.get(course["url"])

                wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "#region-main, .course-content")
                    )
                )

                if "course/view.php" not in driver.current_url:
                    continue

                time.sleep(2)

                # ======================
                # DOSEN
                # ======================
                dosen = course.get("dosen", "Tidak ditemukan")

                if dosen == "Tidak ditemukan":
                    fallback = extract_dosen_names_from_course_page(driver, wait)
                    if fallback:
                        dosen = ", ".join(fallback)

                # ======================
                # SECTION & ACTIVITY
                # ======================
                sections = driver.find_elements(
                    By.CSS_SELECTOR, "li.section.course-section"
                )

                activities = driver.find_elements(
                    By.CSS_SELECTOR, "li.activity"
                )

                counts = {
                    "attendance": 0,
                    "forum": 0,
                    "quiz": 0,
                    "assignment": 0,
                    "label": 0,
                    "file": 0,
                    "link": 0,
                }

                for act in activities:
                    cls = act.get_attribute("class") or ""

                    if "modtype_attendance" in cls:
                        counts["attendance"] += 1
                    if "modtype_forum" in cls:
                        counts["forum"] += 1
                    if "modtype_quiz" in cls:
                        counts["quiz"] += 1
                    if "modtype_assign" in cls:
                        counts["assignment"] += 1
                    if "modtype_label" in cls:
                        counts["label"] += 1
                    if "modtype_resource" in cls:
                        counts["file"] += 1
                    if "modtype_url" in cls:
                        counts["link"] += 1

                # ======================
                # SIMPAN HASIL
                # ======================
                results.append([
                    tahun_obj["nama"],
                    prodi_obj["nama"],
                    semester["nama"],
                    course["nama"],
                    dosen,
                    len(sections),
                    counts["attendance"],
                    counts["forum"],
                    counts["quiz"],
                    counts["assignment"],
                    counts["label"],
                    counts["file"],
                    counts["link"],
                ])

    finally:
        driver.quit()

    return results