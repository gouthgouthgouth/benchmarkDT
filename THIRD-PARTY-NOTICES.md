# Third-Party Notices

This project makes use of the following third-party software. Each component
is listed with its license, copyright holder, and a reference to the official
license text. All licenses were verified directly from the respective upstream
repositories.

---

## Infrastructure and Brokers

### Eclipse Ditto

- **License:** Eclipse Public License 2.0 (EPL-2.0)
- **Copyright:** Eclipse Foundation
- **Repository:** https://github.com/eclipse-ditto/ditto
- **License file:** https://github.com/eclipse-ditto/ditto/blob/master/LICENSE

Eclipse Ditto is used as the Digital Twin broker. The EPL-2.0 is a
weak-copyleft license. No Secondary License option is exercised by the Ditto
project.

---

### FIWARE Orion-LD

- **License:** GNU Affero General Public License v3.0 only (AGPL-3.0-only)
- **Copyright:** FIWARE Foundation e.V.
- **Repository:** https://github.com/FIWARE/context.Orion-LD
- **License file:** https://github.com/FIWARE/context.Orion-LD/blob/develop/LICENSE

Orion-LD is used as an NGSI-LD context broker. The AGPL-3.0 requires that
the complete corresponding source code be made available if the software is
used to provide a network service.

---

### FIWARE IoT Agent for JSON

- **License:** GNU Affero General Public License v3.0 only (AGPL-3.0-only)
- **Copyright:** Telefonica Investigación y Desarrollo, S.A.U
- **Repository:** https://github.com/telefonicaid/iotagent-json
- **License file:** https://github.com/telefonicaid/iotagent-json/blob/master/LICENSE

The IoT Agent for JSON is used to bridge MQTT messages to the NGSI-LD brokers
(Orion-LD and Scorpio). Same AGPL-3.0 obligations apply as above.

---

### Scorpio Broker

- **License:** BSD 3-Clause License
- **Copyright:** Copyright (c) 2021, NEC
- **Repository:** https://github.com/ScorpioBroker/ScorpioBroker
- **License file:** https://github.com/ScorpioBroker/ScorpioBroker/blob/development/LICENSE

Scorpio is used as an alternative NGSI-LD context broker.

---

### Eclipse Mosquitto

- **License:** Eclipse Public License 2.0 OR Eclipse Distribution License 1.0
  (EPL-2.0 OR BSD-3-Clause)
- **Copyright:** Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors
- **Repository:** https://github.com/eclipse-mosquitto/mosquitto
- **License file:** https://github.com/eclipse-mosquitto/mosquitto/blob/master/LICENSE.txt

Eclipse Mosquitto is used as the MQTT message broker. It is dual-licensed;
consumers may choose to comply with either the EPL-2.0 or the EDL-1.0
(Eclipse Distribution License 1.0, which is functionally equivalent to the
BSD 3-Clause license).

---

### MongoDB (Community Edition, v4.4)

- **License:** Server Side Public License, Version 1 (SSPL-1.0)
- **Copyright:** Copyright © 2018 MongoDB, Inc.
- **Repository:** https://github.com/mongodb/mongo
- **License file:** https://github.com/mongodb/mongo/blob/v4.4/LICENSE-Community.txt

MongoDB 4.4 is used as the backing database for Orion-LD and the IoT Agent.
MongoDB switched from AGPL-3.0 to SSPL-1.0 starting with version 4.0
(October 2018). SSPL-1.0 is not an OSI-approved open-source license. If
MongoDB is offered as a service to third parties, the SSPL-1.0 requires making
the complete source code of the entire service stack publicly available.

---

### PostGIS

- **License:** GNU General Public License v2.0 (GPL-2.0)
- **Copyright:** PostGIS project contributors (community-maintained; no single
  corporate copyright holder)
- **Repository:** https://github.com/postgis/postgis
- **License file:** https://github.com/postgis/postgis/blob/master/COPYING

PostGIS (`postgis/postgis` Docker image) is used as the database backend for
the Scorpio Broker. Note that PostGIS bundles several dependencies (GEOS,
Proj, GDAL, LibXML) under their own licenses (LGPL, MIT); see
`LICENSE.TXT` in the repository for details.

---

## Python Dependencies

The following Python libraries are listed in `requirements.txt` or are
imported directly by the project source code.

---

### matplotlib

- **Version used:** 3.10.8
- **License:** Custom PSF-compatible license (PSF-2.0;
  PyPI classifier: "PSF-style / Python Software Foundation License")
- **Copyright:**
  - Version 1.3.0 and later: Copyright (c) 2012– Matplotlib Development Team;
    All Rights Reserved
  - Version 1.2.x and earlier: Copyright (c) 2002–2011 John D. Hunter;
    All Rights Reserved
- **Repository:** https://github.com/matplotlib/matplotlib
- **License file:** https://github.com/matplotlib/matplotlib/blob/main/LICENSE/LICENSE

The matplotlib license is a permissive, BSD-style agreement specific to the
project. It is compatible with the Python Software Foundation license.

---

### numpy

- **Version used:** 2.4.2
- **License:** BSD 3-Clause License
- **Copyright:** Copyright (c) 2005–2025, NumPy Developers
- **Repository:** https://github.com/numpy/numpy
- **License file:** https://github.com/numpy/numpy/blob/main/LICENSE.txt

---

### paho-mqtt (Eclipse Paho MQTT Python Client)

- **Version used:** 2.1.0
- **License:** Eclipse Public License 2.0 OR Eclipse Distribution License 1.0
  (EPL-2.0 OR BSD-3-Clause)
- **Copyright:** Copyright (c) Eclipse Foundation, Inc. and its licensors
- **Repository:** https://github.com/eclipse-paho/paho.mqtt.python
- **License file:** https://github.com/eclipse-paho/paho.mqtt.python/blob/master/LICENSE.txt

Dual-licensed under EPL-2.0 and EDL-1.0, the same scheme as Eclipse
Mosquitto above.

---

### pandas

- **Version used:** 3.0.0
- **License:** BSD 3-Clause License
- **Copyright:**
  - Copyright (c) 2008–2011, AQR Capital Management, LLC, Lambda Foundry, Inc.
    and PyData Development Team
  - Copyright (c) 2011–2026, Open source contributors
- **Repository:** https://github.com/pandas-dev/pandas
- **License file:** https://github.com/pandas-dev/pandas/blob/main/LICENSE

---

### requests

- **Version used:** 2.32.5
- **License:** Apache License 2.0 (Apache-2.0)
- **Copyright:** Copyright 2019 Kenneth Reitz
- **Repository:** https://github.com/psf/requests
- **License file:** https://github.com/psf/requests/blob/main/LICENSE

---

### seaborn

- **Version used:** (unpinned in requirements.txt)
- **License:** BSD 3-Clause License
- **Copyright:** Copyright (c) 2012–2023, Michael L. Waskom
- **Repository:** https://github.com/mwaskom/seaborn
- **License file:** https://github.com/mwaskom/seaborn/blob/master/LICENSE.md

---

## Standard Library

The following modules are part of the Python standard library and are
distributed under the **Python Software Foundation License (PSF-2.0)**:
`atexit`, `collections`, `copy`, `csv`, `datetime`, `glob`, `itertools`,
`json`, `logging`, `math`, `multiprocessing`, `os`, `pprint`, `random`,
`re`, `signal`, `string`, `subprocess`, `time`, `zoneinfo`.

Python PSF License: https://docs.python.org/3/license.html

---

*All license information was verified directly from the upstream repository
LICENSE files at the time of writing. Licenses are subject to change by
upstream maintainers; always refer to the official repositories for the most
current terms.*
