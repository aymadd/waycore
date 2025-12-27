# Third-Party Attributions

**Version**: 1.0.0\
**Last Updated**: December 2024

This document lists all major third-party software, models, datasets, and
resources used in Waycore for attribution and licensing purposes.

---

## Table of Contents

- [AI Models](#ai-models)
- [Python Dependencies](#python-dependencies)
- [UI Framework](#ui-framework)
- [Infrastructure](#infrastructure)
- [Knowledge Base Sources](#knowledge-base-sources)
- [Datasets & Labels](#datasets--labels)
- [License Summary](#license-summary)

---

## AI Models

### Language Models

| Model                  | Author         | License       | Source                                                                      |
| ---------------------- | -------------- | ------------- | --------------------------------------------------------------------------- |
| Phi-3 Mini 4K Instruct | Microsoft      | MIT           | [HuggingFace](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf) |
| TinyLlama 1.1B         | TinyLlama Team | Apache 2.0    | [HuggingFace](https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0)    |
| Gemma 2B               | Google         | Gemma License | [HuggingFace](https://huggingface.co/google/gemma-2b-it)                    |

### Vision Models

| Model                 | Author             | License    | Source                                                                                          |
| --------------------- | ------------------ | ---------- | ----------------------------------------------------------------------------------------------- |
| MobileNetV3 Small     | Google             | Apache 2.0 | [TensorFlow Hub](https://tfhub.dev/google/imagenet/mobilenet_v3_small_100_224/classification/5) |
| iNaturalist ResNet-50 | Zenodo/iNaturalist | CC-BY      | [Zenodo](https://zenodo.org/records/10066893)                                                   |

### Embedding Models

| Model            | Author                | License    | Source                                                                       |
| ---------------- | --------------------- | ---------- | ---------------------------------------------------------------------------- |
| all-MiniLM-L6-v2 | Sentence Transformers | Apache 2.0 | [HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) |

### Inference Engines

| Library         | Author          | License    | Source                                           |
| --------------- | --------------- | ---------- | ------------------------------------------------ |
| llama.cpp       | Georgi Gerganov | MIT        | [GitHub](https://github.com/ggerganov/llama.cpp) |
| TensorFlow Lite | Google          | Apache 2.0 | [TensorFlow](https://www.tensorflow.org/lite)    |

---

## Python Dependencies

### Core Libraries

| Package                                                          | Author             | License      | Purpose           |
| ---------------------------------------------------------------- | ------------------ | ------------ | ----------------- |
| [Pydantic](https://pydantic.dev/)                                | Samuel Colvin      | MIT          | Data validation   |
| [FastAPI](https://fastapi.tiangolo.com/)                         | Sebastián Ramírez  | MIT          | Web framework     |
| [Uvicorn](https://www.uvicorn.org/)                              | Encode             | BSD-3-Clause | ASGI server       |
| [httpx](https://www.python-httpx.org/)                           | Encode             | BSD-3-Clause | HTTP client       |
| [aiosqlite](https://github.com/omnilib/aiosqlite)                | Amethyst Reese     | MIT          | Async SQLite      |
| [Paho MQTT](https://eclipse.dev/paho/)                           | Eclipse Foundation | EPL 2.0      | MQTT client       |
| [PyYAML](https://pyyaml.org/)                                    | Kirill Simonov     | MIT          | YAML parsing      |
| [Pillow](https://python-pillow.org/)                             | Jeffrey A. Clark   | HPND         | Image processing  |
| [python-multipart](https://github.com/andrew-d/python-multipart) | Andrew Dunham      | Apache 2.0   | Form data parsing |
| [typing-extensions](https://github.com/python/typing_extensions) | Python             | PSF          | Type hints        |

### AI & ML Libraries

| Package                                      | Author    | License    | Purpose          |
| -------------------------------------------- | --------- | ---------- | ---------------- |
| [ChromaDB](https://www.trychroma.com/)       | Chroma    | Apache 2.0 | Vector database  |
| [sentence-transformers](https://sbert.net/)  | UKP Lab   | Apache 2.0 | Text embeddings  |
| [hnswlib](https://github.com/nmslib/hnswlib) | NMS Lab   | Apache 2.0 | Vector search    |
| [PyMuPDF](https://pymupdf.readthedocs.io/)   | Artifex   | AGPL 3.0   | PDF parsing      |
| [MCP](https://modelcontextprotocol.io/)      | Anthropic | MIT        | AI tool protocol |

### Development Tools

| Package                                          | Author          | License | Purpose          |
| ------------------------------------------------ | --------------- | ------- | ---------------- |
| [pytest](https://pytest.org/)                    | Pytest Team     | MIT     | Testing          |
| [Ruff](https://docs.astral.sh/ruff/)             | Astral          | MIT     | Linting          |
| [Black](https://black.readthedocs.io/)           | Łukasz Langa    | MIT     | Code formatting  |
| [mypy](https://mypy-lang.org/)                   | Python          | MIT     | Type checking    |
| [Hypothesis](https://hypothesis.readthedocs.io/) | Hypothesis Team | MPL 2.0 | Property testing |

---

## UI Framework

| Package                                     | Author     | License               | Purpose            |
| ------------------------------------------- | ---------- | --------------------- | ------------------ |
| [PySide6](https://doc.qt.io/qtforpython-6/) | Qt Company | LGPL 3.0 / Commercial | Python Qt bindings |
| [Qt 6 / QML](https://www.qt.io/)            | Qt Company | LGPL 3.0 / Commercial | UI framework       |

### Fonts

| Font           | Author  | License | Usage   |
| -------------- | ------- | ------- | ------- |
| System Default | Various | Various | UI text |

---

## Infrastructure

### Containerization

| Tool                                               | Author       | License    | Source                        |
| -------------------------------------------------- | ------------ | ---------- | ----------------------------- |
| [Docker](https://www.docker.com/)                  | Docker, Inc. | Apache 2.0 | Container runtime             |
| [Docker Compose](https://docs.docker.com/compose/) | Docker, Inc. | Apache 2.0 | Multi-container orchestration |

### Message Broker

| Tool                                        | Author             | License | Source      |
| ------------------------------------------- | ------------------ | ------- | ----------- |
| [Eclipse Mosquitto](https://mosquitto.org/) | Eclipse Foundation | EPL 2.0 | MQTT broker |

### Database

| Tool                          | Author          | License       | Source            |
| ----------------------------- | --------------- | ------------- | ----------------- |
| [SQLite](https://sqlite.org/) | D. Richard Hipp | Public Domain | Embedded database |

---

## Knowledge Base Sources

The RAG (Retrieval-Augmented Generation) knowledge base for outdoor survival,
navigation, first aid, and related topics is maintained in a separate
repository:

**[waycore-knowledge](https://github.com/dmitry-grechko/waycore-knowledge)** — A
curated collection of ~7,000 entries from 40+ public domain and Creative
Commons-licensed sources including:

- 🪖 **Survival**: US Army FM 21-76, Ranger Handbook, and related manuals
- 🧭 **Navigation**: FM 3-25.26 Map Reading, USGS topographic guides
- 🏥 **First Aid**: FM 4-25.11, BSA Wilderness First Aid
- 🌿 **Plants**: USDA Plants Database, Plants For A Future (PFAF)
- 🪢 **Knots**: FM 5-125 Rigging, Army Mountain Warfare guides
- 🌦️ **Weather**: NOAA Cloud Chart, NWS Weather Spotter Guide

For complete source attributions and licensing details, see
[SOURCES.md](https://github.com/dmitry-grechko/waycore-knowledge/blob/main/SOURCES.md)
in the waycore-knowledge repository

---

## Datasets & Labels

| Dataset          | Author             | License | Purpose                |
| ---------------- | ------------------ | ------- | ---------------------- |
| ImageNet Labels  | Stanford/Princeton | Various | Object classification  |
| iNaturalist 2021 | iNaturalist/Kaggle | CC-BY   | Species identification |

---

## License Summary

| License          | Count | Type            |
| ---------------- | ----- | --------------- |
| MIT              | 15+   | Permissive      |
| Apache 2.0       | 10+   | Permissive      |
| LGPL 3.0         | 2     | Copyleft (weak) |
| Public Domain    | 10+   | Unrestricted    |
| Creative Commons | 5+    | Various         |
| EPL 2.0          | 2     | Copyleft (weak) |
| AGPL 3.0         | 1     | Strong copyleft |

### License Compatibility Notes

- **AGPL 3.0 (PyMuPDF)**: Used for PDF parsing in RAG index building. The
  network copyleft provisions apply to the indexing process. Alternative parsers
  may be substituted if needed.

- **LGPL 3.0 (Qt/PySide6)**: Dynamic linking is used; no modifications to Qt
  source. Users may substitute their own Qt installation.

- **EPL 2.0 (Mosquitto, Paho)**: Compatible with other open-source licenses for
  combined works.

---

## Acknowledgments

Waycore is made possible by the incredible work of open-source developers and
organizations worldwide. We are grateful to:

- The **Python Software Foundation** for Python
- **Microsoft** for Phi-3 language models
- **Google/TensorFlow** for MobileNet and TensorFlow Lite
- **iNaturalist** and the **California Academy of Sciences** for species data
- The **Qt Company** for Qt and PySide6
- **Eclipse Foundation** for Mosquitto MQTT
- Contributors to the
  [waycore-knowledge](https://github.com/dmitry-grechko/waycore-knowledge)
  repository and all public domain source materials
- All individual contributors to the packages listed above

---

## Reporting Issues

If you believe there is a licensing issue or missing attribution, please open an
issue on the Waycore repository or contact the maintainers.

---

_This document is provided for informational purposes. For definitive licensing
information, refer to the LICENSE files of individual packages and resources._
