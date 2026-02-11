#!/usr/bin/env python3
import hashlib
import random
import uuid
import requests

BASE_URL = "https://securepay.tinkoff.ru/v2"

PRODUCTS = [
    "Футболка", "Кружка", "Блокнот", "Наушники", "Чехол",
    "Подарочная карта", "Книга", "USB кабель", "Зарядка"
]


def generate_token(params: dict, password: str) -> str:
    filtered = {k: v for k, v in params.items() if not isinstance(v, (dict, list)) and k != "Token"}
    filtered["Password"] = password
    concat = "".join(str(filtered[k]) for k in sorted(filtered.keys()))
    return hashlib.sha256(concat.encode("utf-8")).hexdigest()


def init_payment(terminal_key: str, password: str, with_receipt: bool = False,
                  email: str = "test@example.com", amount: int = None) -> dict:
    product = random.choice(PRODUCTS)
    price = random.randint(10000, 100000)
    quantity = random.randint(1, 3)

    if amount is not None:
        price = amount
        quantity = 1

    total = price * quantity

    params = {
        "TerminalKey": terminal_key,
        "Amount": total,
        "OrderId": str(uuid.uuid4())[:36],
        "Description": product,
        "DATA": {"Email": email},
    }

    if with_receipt:
        params["Receipt"] = {
            "Email": email,
            "Taxation": "usn_income",
            "Items": [
                {
                    "Name": product,
                    "Price": price,
                    "Quantity": quantity,
                    "Amount": total,
                    "Tax": "none",
                    "PaymentMethod": "full_payment",
                    "PaymentObject": "commodity"
                }
            ]
        }

    params["Token"] = generate_token(params, password)
    return requests.post(f"{BASE_URL}/Init", json=params).json()


def cancel_payment(terminal_key: str, password: str, payment_id: str) -> dict:
    params = {"TerminalKey": terminal_key, "PaymentId": payment_id}
    params["Token"] = generate_token(params, password)
    return requests.post(f"{BASE_URL}/Cancel", json=params).json()


def create_real_payment(terminal_key: str, password: str):
    print("\n" + "=" * 40)
    print("  Создание реального платежа")
    print("=" * 40)

    # Email
    email_choice = input("\nУказать свою почту? (y/n, по умолчанию test@example.com): ").strip().lower()
    if email_choice == 'y':
        email = input("Email: ").strip()
        if not email:
            print("Пустой email, используется test@example.com")
            email = "test@example.com"
    else:
        email = "test@example.com"

    # Сумма
    amount_choice = input("\nУказать свою сумму? (y/n, по умолчанию случайная): ").strip().lower()
    custom_amount = None
    if amount_choice == 'y':
        raw = input("Сумма в рублях (например 150.50): ").strip()
        try:
            custom_amount = int(float(raw) * 100)  # в копейки
            if custom_amount <= 0:
                print("Сумма должна быть > 0, используется случайная")
                custom_amount = None
        except ValueError:
            print("Некорректная сумма, используется случайная")
            custom_amount = None

    # Чек
    receipt_choice = input("\nНужен чек? (y/n, по умолчанию нет): ").strip().lower()
    with_receipt = receipt_choice == 'y'

    # Подтверждение
    print("\n--- Параметры платежа ---")
    print(f"  Email: {email}")
    if custom_amount is not None:
        print(f"  Сумма: {custom_amount / 100:.2f} руб.")
    else:
        print("  Сумма: случайная")
    print(f"  Чек: {'да' if with_receipt else 'нет'}")
    print("-------------------------")

    confirm = input("\nСоздать платеж? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Отменено.")
        return

    resp = init_payment(terminal_key, password, with_receipt=with_receipt,
                        email=email, amount=custom_amount)
    if resp.get("Success"):
        print(f"\nПлатеж создан!")
        print(f"  PaymentId: {resp.get('PaymentId')}")
        print(f"  Сумма: {resp.get('Amount', 0) / 100:.2f} руб.")
        print(f"  Статус: {resp.get('Status')}")
        print(f"  URL оплаты: {resp.get('PaymentURL')}")
    else:
        print(f"\nОшибка: {resp.get('Message')} (код: {resp.get('ErrorCode')})")
    wait_continue()


def wait_continue():
    input("\n>>> Нажмите Enter для продолжения...")


def test_1(terminal_key: str, password: str):
    print("\n[Тест 1] Создание платежа")
    resp = init_payment(terminal_key, password)
    if resp.get("Success"):
        print(f"PaymentId: {resp.get('PaymentId')}")
        print(f"URL: {resp.get('PaymentURL')}")
    else:
        print(f"Ошибка: {resp.get('Message')}")
    wait_continue()


def test_2(terminal_key: str, password: str):
    print("\n[Тест 2] Создание платежа для оплаты тестовой картой")
    resp = init_payment(terminal_key, password)
    if resp.get("Success"):
        print(f"PaymentId: {resp.get('PaymentId')}")
        print(f"URL: {resp.get('PaymentURL')}")
        print("Оплатите тестовой картой")
    else:
        print(f"Ошибка: {resp.get('Message')}")
    wait_continue()


def test_3(terminal_key: str, password: str):
    print("\n[Тест 3] Создание платежа для оплаты и отмены")
    resp = init_payment(terminal_key, password)
    if not resp.get("Success"):
        print(f"Ошибка: {resp.get('Message')}")
        return

    payment_id = resp.get("PaymentId")
    print(f"PaymentId: {payment_id}")
    print(f"URL: {resp.get('PaymentURL')}")
    print("Оплатите тестовой картой")
    wait_continue()

    print("Отмена платежа...")
    cancel_resp = cancel_payment(terminal_key, password, str(payment_id))
    if cancel_resp.get("Success"):
        print(f"Статус: {cancel_resp.get('Status')}")
    else:
        print(f"Ошибка: {cancel_resp.get('Message')}")
    wait_continue()


def test_7(terminal_key: str, password: str):
    print("\n[Тест 7] Создание платежа с чеком")
    resp = init_payment(terminal_key, password, with_receipt=True)
    if resp.get("Success"):
        print(f"PaymentId: {resp.get('PaymentId')}")
        print(f"URL: {resp.get('PaymentURL')}")
    else:
        print(f"Ошибка: {resp.get('Message')}")
    wait_continue()


def test_8(terminal_key: str, password: str):
    while True:
        print("\n[Тест 8] Создание платежа и отмена")
        resp = init_payment(terminal_key, password)
        if not resp.get("Success"):
            print(f"Ошибка: {resp.get('Message')}")
            return

        payment_id = resp.get("PaymentId")
        print(f"PaymentId: {payment_id}")
        print(f"URL: {resp.get('PaymentURL')}")
        wait_continue()

        print("Отмена платежа...")
        cancel_resp = cancel_payment(terminal_key, password, str(payment_id))
        if cancel_resp.get("Success"):
            print(f"Статус: {cancel_resp.get('Status')}")
        else:
            print(f"Ошибка: {cancel_resp.get('Message')}")

        choice = input("\nПовторить тест 8? (y/n): ").strip().lower()
        if choice != 'y':
            break


def run_all_tests(terminal_key: str, password: str):
    test_1(terminal_key, password)
    test_2(terminal_key, password)
    test_3(terminal_key, password)
    test_7(terminal_key, password)
    test_8(terminal_key, password)


def show_menu():
    print("\n1 - Тест 1")
    print("2 - Тест 2")
    print("3 - Тест 3")
    print("7 - Тест 7 (с чеком)")
    print("8 - Тест 8")
    print("9 - Создать реальный платеж (свои параметры)")
    print("0 - Все тесты по порядку")
    print("q - Выход")


def run_single_test(terminal_key: str, password: str, test_num: str):
    tests = {
        "1": test_1,
        "2": test_2,
        "3": test_3,
        "7": test_7,
        "8": test_8,
        "9": create_real_payment,
    }
    if test_num in tests:
        tests[test_num](terminal_key, password)


def main():
    print("=" * 40)
    print("  T-Bank Terminal Test")
    print("=" * 40)

    terminal_key = input("\nTerminal ID: ").strip()
    password = input("Пароль: ").strip()

    if not terminal_key or not password:
        print("Ошибка: заполните все поля")
        return

    while True:
        show_menu()
        choice = input("\nВыбор: ").strip().lower()

        if choice == 'q':
            break
        elif choice == '0':
            run_all_tests(terminal_key, password)
            print("\nВсе тесты завершены")
        elif choice in ['1', '2', '3', '7', '8', '9']:
            run_single_test(terminal_key, password, choice)
        else:
            print("Неверный выбор")

    print("Готово!")


if __name__ == "__main__":
    main()
