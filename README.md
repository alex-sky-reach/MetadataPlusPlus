# Metadata++

An advanced **Calibre Metadata Download** plugin that searches multiple online providers and intelligently combines the best metadata available.

This project was created to improve metadata quality when importing ebooks into Calibre, especially when dealing with books in multiple languages.

> ⚠️ This is my very first programming project and my first GitHub repository.

Although I have **no formal programming background**, I was able to build this plugin thanks to modern AI tools, a lot of curiosity, countless hours of testing, and many iterations.

The goal of this project is simple:

> Build something useful for myself and hopefully for the whole Calibre community.

---

# Features

✔ Amazon support (browser-assisted)

✔ Goodreads support

✔ Google Books support

✔ OpenLibrary support

✔ ISBNDB support

✔ Multiple providers working together

✔ Intelligent weighted scoring

✔ Automatic best-match selection

✔ Configurable source priorities

✔ Browser fallback when required

✔ Works with large Calibre libraries

---

# Screenshots

## Sources

<img width="1560" height="1550" alt="sources Metadata++" src="https://github.com/user-attachments/assets/a3e1d051-828d-471f-84e7-f8d74c30d77b" />

---

## Source Weights

<img width="1572" height="1566" alt="sources weights Metadata++" src="https://github.com/user-attachments/assets/71aed99b-56ef-42d9-979e-f705a0a5fb73" />

---

## Results

<img width="1578" height="1284" alt="result 1 Metadata++" src="https://github.com/user-attachments/assets/7b2d6ffb-009a-428a-8dc8-f33f49443603" />

<img width="1582" height="1280" alt="result 2 Metadata++" src="https://github.com/user-attachments/assets/9407c18b-a9a5-4451-8503-0c98bec13177" />

---

## Browser fallback settings

<img width="1860" height="1544" alt="browser fallback Metadata++" src="https://github.com/user-attachments/assets/0116372d-33d9-437d-b65d-a35c2541f424" />


---

# Installation

Download the latest release.

Inside Calibre:

Preferences

→ Plugins

→ Load plugin from file

Select

```
Metadata++.zip
```

Restart Calibre.

---

# Browser requirements

Amazon actively protects against automated scraping.

For best compatibility install:

- Python 3
- Playwright
- Firefox browser for Playwright

Chrome was intentionally avoided because Firefox proved to be much more reliable.

---

# Why this project exists

Calibre already has an excellent metadata download system.

However, I wanted:

- more metadata providers
- weighted providers
- better matching
- browser-assisted Amazon scraping
- more control over the metadata sources

This project was born from those ideas.

---

# AI Disclosure

This plugin was developed with the assistance of AI.

I do **not** consider myself a programmer.

Instead, I used AI as a development assistant while continuously:

- testing
- debugging
- reading the generated code
- understanding what it was doing
- requesting improvements
- finding bugs
- refining the design

Every feature was tested manually inside Calibre.

---

# Credits

Huge thanks to the Calibre community.

Special thanks to:

- kovidgoyal for creating Calibre.
- MobileRead contributors.
- Metadata+ author (jadehawk) for inspiration and valuable technical advice.

Without those resources this project would not exist.

---

# Contributing

Bug reports, ideas, pull requests and suggestions are always welcome.

If you find a bug, please open an Issue.

If you'd like to improve the plugin, feel free to submit a Pull Request.

---

# Disclaimer

This plugin accesses publicly available metadata from third-party providers.

Availability of providers may change over time.

Amazon may temporarily rate-limit requests if large libraries are scanned repeatedly.

Use responsibly.

---

# License

MIT License
