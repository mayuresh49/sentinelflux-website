.PHONY: web web-fast api

# Run web tests in parallel with session-scoped login
web:
	python3 -m pytest tests/web/ -m web -n 4 --session-login

# Run web tests serially (debug / CI with limited resources)
web-serial:
	python3 -m pytest tests/web/ -m web

# Run API tests
api:
	python3 -m pytest tests/api/ -m api
