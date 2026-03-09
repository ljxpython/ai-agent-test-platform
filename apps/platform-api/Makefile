.PHONY: dev-up dev-down dev-check

dev-up:
	bash scripts/dev_tunnel_up.sh

dev-down:
	bash scripts/dev_tunnel_down.sh

dev-check:
	curl -sS -o /dev/null -w 'health:%{http_code}\n' http://127.0.0.1:2024/_proxy/health
	curl -sS -o /dev/null -w 'runtime:%{http_code}\n' http://127.0.0.1:8123/info
