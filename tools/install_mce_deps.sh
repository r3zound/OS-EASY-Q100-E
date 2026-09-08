#!/bin/bash
pip3 install --quiet pltable colorama 2>&1 | tail -3
python3 -c "import pltable; print('pltable OK')"
