.PHONY: web web-serial api \
        orangehrm-web orangehrm-api \
        restfulbooker-web restfulbooker-api \
        framework-tests

# ── OrangeHRM ──────────────────────────────────────────────────────────────
orangehrm-web:
	cd products/orangehrm && python3 -m pytest tests/web/ -m web -n 4 --session-login

orangehrm-web-serial:
	cd products/orangehrm && python3 -m pytest tests/web/ -m web

orangehrm-api:
	cd products/orangehrm && python3 -m pytest tests/api/ -m api

# ── Restful Booker ──────────────────────────────────────────────────────────
restfulbooker-web:
	cd products/restfulbooker && python3 -m pytest tests/web/ -m web -n 4

restfulbooker-web-serial:
	cd products/restfulbooker && python3 -m pytest tests/web/ -m web

restfulbooker-api:
	cd products/restfulbooker && python3 -m pytest tests/api/ -m api

# ── Framework unit/integration tests ───────────────────────────────────────
framework-tests:
	python3 -m pytest tests/ -q

# ── Legacy aliases (kept for CI compatibility) ─────────────────────────────
web:
	$(MAKE) orangehrm-web

web-serial:
	$(MAKE) orangehrm-web-serial

api:
	$(MAKE) orangehrm-api
