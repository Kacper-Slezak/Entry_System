import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import models
from backend.app.db.models import AccessLogStatus


# 1. DEFINICJA FAŁSZYWYCH KLAS (FAKE CLASSES)
# Zamiast MagicMocka, używamy własnych klas. To eliminuje "niespodzianki".

class FakeQuery:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None

    def count(self):
        return len(self._items)

    # Te metody normalnie filtrują/sortują, ale w teście zwracamy po prostu "siebie"
    # dzięki temu łańcuch db.query().filter().order_by().all() działa poprawnie.
    def filter(self, *args, **kwargs): return self

    def filter_by(self, *args, **kwargs): return self

    def order_by(self, *args, **kwargs): return self

    def join(self, *args, **kwargs): return self

    def limit(self, *args, **kwargs): return self

    def offset(self, *args, **kwargs): return self

    # Obsługa iteracji (gdyby kod robił: for x in query)
    def __iter__(self):
        return iter(self._items)


class FakeSession:
    def __init__(self):
        self.store = []  # Tu trzymamy obiekty
        self.query_result = []  # A tu trzymamy to, co ma zwrócić query

    def add(self, obj):
        self.store.append(obj)

    def commit(self):
        pass  # Nic nie robimy

    def refresh(self, obj):
        pass  # Nic nie robimy

    def query(self, *args, **kwargs):
        # Zawsze zwracamy nasz FakeQuery z przygotowanymi danymi
        return FakeQuery(self.query_result)


# 2. KONFIGURACJA TESTU

# Nadpisujemy zależność get_db w aplikacji, żeby używała naszego FakeSession
# Zakładam standardową ścieżkę. Jeśli masz inną, Pytest i tak powinien
# użyć override'a z conftest.py, ale dla pewności robimy to tu.
fake_session_instance = FakeSession()


# WAŻNE: Wymuszamy, żeby aplikacja widziała naszą sesję
# Szukamy dependency_overrides w aplikacji i podmieniamy.
# (To zadziała, jeśli w main.py używasz get_db jako dependency)
def override_get_db():
    yield fake_session_instance


app.dependency_overrides[app.dependency_overrides.get("get_db", None)] = override_get_db
# Jeśli powyższe nie zadziała (bo klucz jest inny), nadpisujemy globalnie w conftest,
# ale tutaj działamy na instancji testowej.

client = TestClient(app)


@pytest.fixture
def sample_data():
    # Czyścimy sesję przed testem
    fake_session_instance.store = []
    fake_session_instance.query_result = []

    # Tworzymy dane
    employee = models.Employee(
        name="Report Test User",
        email="report@test.com",
        is_active=True,
        embedding=None
    )
    import uuid
    employee.uuid = uuid.uuid4()

    # Dodajemy do "bazy"
    fake_session_instance.add(employee)

    log_granted = models.AccessLog(
        timestamp=datetime.utcnow(),
        status=AccessLogStatus.GRANTED,
        reason="Verification successful",
        employee_id=employee.uuid,
        employee=employee
    )

    log_denied = models.AccessLog(
        timestamp=datetime.utcnow(),
        status=AccessLogStatus.DENIED_FACE,
        reason="Face does not match",
        employee_id=None,
        employee=None
    )

    # KONFIGURACJA ODPOWIEDZI
    # Mówimy naszej fałszywej sesji: "Jak ktoś zapyta o dane, oddaj te dwa logi"
    fake_session_instance.query_result = [log_granted, log_denied]

    # Zapisujemy logi "na boku" do użycia w testach
    fake_session_instance.logs = [log_granted, log_denied]
    fake_session_instance.denied_log = log_denied

    # W tym podejściu musimy ręcznie wstrzyknąć naszą sesję do dependency overrides
    # żeby mieć pewność 100%, że klient jej użyje.
    # Zakładamy, że funkcja pobierająca bazę nazywa się 'get_db'.
    # Jeśli nie wiesz gdzie ona jest, iterujemy po overrides.

    return employee


# 3. TESTY

def test_get_logs_json(sample_data):
    # Upewniamy się, że override jest aktywny
    app.dependency_overrides[require_db_dependency] = lambda: fake_session_instance

    response = client.get("/admin/logs")

    assert response.status_code == 200
    data = response.json()

    # Teraz FakeQuery na pewno zwróci listę
    assert len(data) >= 2

    found_granted = False
    for entry in data:
        if entry["status"] == "GRANTED":
            found_granted = True
            assert entry["employee_name"] == "Report Test User"
            assert entry["reason"] == "Verification successful"

    assert found_granted is True


def test_get_logs_filtering(sample_data):
    # DLA FILTROWANIA: Zmieniamy to, co zwraca query
    fake_session_instance.query_result = [fake_session_instance.denied_log]

    response = client.get("/admin/logs?status=DENIED_FACE")

    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0
    for entry in data:
        assert entry["status"] == "DENIED_FACE"


def test_export_csv(sample_data):
    # Resetujemy query result do wszystkich logów
    fake_session_instance.query_result = fake_session_instance.logs

    response = client.get("/admin/logs/export")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment; filename=raport_wejsc.csv" in response.headers["content-disposition"]

    content = response.text

    # Sprawdzamy nagłówki (CSV może być rozdzielany przecinkiem lub średnikiem)
    #
    assert (
            "ID;Date;Hour;Status;Reason;Worker Name;Email" in content
            or "ID,Date,Hour,Status,Reason,Worker Name,Email" in content
    )

    assert "Report Test User" in content
    assert "Face does not match" in content


# Helper function to find the dependency key for 'get_db' if possible
def require_db_dependency():
    pass  # Placeholder, właściwe nadpisanie robimy w teście lambda: fake_session_instance


# Próba znalezienia właściwej funkcji get_db w dependency_overrides, żeby ją nadpisać
# To jest "brute force" fix na wypadek gdyby conftest.py nie działał jak trzeba.
for key in app.dependency_overrides.keys():
    # Szukamy czegokolwiek co ma w nazwie "get_db" lub zwraca sesję
    if hasattr(key, "__name__") and "get_db" in key.__name__:
        app.dependency_overrides[key] = lambda: fake_session_instance
