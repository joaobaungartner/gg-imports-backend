import fnmatch
import json
import sys


GLOBAL_THRESHOLD = 80

GROUPS = {
    "Autenticacao/autorizacao": {
        "threshold": 90,
        "patterns": [
            "src/middlewares/auth.py",
            "src/routes/auth_routes.py",
            "src/use_cases/auth/*.py",
            "src/use_cases/user/authenticate_user.py",
            "src/utils/jwt.py",
            "src/utils/password.py",
        ],
    },
    "Pedidos e estoque": {
        "threshold": 90,
        "patterns": [
            "src/entities/order.py",
            "src/entities/order_item.py",
            "src/repositories/order_repository.py",
            "src/repositories/order_item_repository.py",
            "src/repositories/order_status_history_repository.py",
            "src/routes/order_routes.py",
            "src/routes/order_item_routes.py",
            "src/routes/admin_order_routes.py",
            "src/use_cases/order/*.py",
            "src/use_cases/order_item/*.py",
            "src/use_cases/product/*stock*.py",
            "src/use_cases/product/check_product_availability.py",
        ],
    },
    "Pagamentos/webhooks": {
        "threshold": 90,
        "patterns": [
            "src/entities/payment.py",
            "src/repositories/payment_repository.py",
            "src/routes/payment_routes.py",
            "src/services/mercado_pago.py",
            "src/use_cases/payment/*.py",
        ],
    },
}


def matches(path, patterns):
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


with open("coverage.json", encoding="utf-8") as file:
    coverage = json.load(file)

failures = []

global_coverage = coverage["totals"]["percent_covered"]

print()
print("=== Coverage gates ===")
print(f"Global: {global_coverage:.2f}% / minimo {GLOBAL_THRESHOLD}%")

if global_coverage < GLOBAL_THRESHOLD:
    failures.append(
        f"Cobertura global {global_coverage:.2f}% < {GLOBAL_THRESHOLD}%"
    )

for name, config in GROUPS.items():
    statements = 0
    covered = 0

    for path, data in coverage["files"].items():
        if matches(path, config["patterns"]):
            summary = data["summary"]
            statements += summary["num_statements"]
            covered += summary["covered_lines"]

    if statements == 0:
        print(f"{name}: nenhum arquivo encontrado")
        failures.append(f"{name}: nenhum arquivo encontrado")
        continue

    percentage = covered / statements * 100
    threshold = config["threshold"]

    print(f"{name}: {percentage:.2f}% / minimo {threshold}%")

    if percentage < threshold:
        failures.append(
            f"{name}: {percentage:.2f}% < {threshold}%"
        )

print()

if failures:
    print("Coverage insuficiente:")
    for failure in failures:
        print(f"- {failure}")

    sys.exit(1)

print("Todas as metas de cobertura foram atingidas.")
