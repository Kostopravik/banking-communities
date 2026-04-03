/// Базовый URL FastAPI. Для Android-эмулятора: --dart-define=API_BASE=http://10.0.2.2:8001
const String kApiBase = String.fromEnvironment(
  'API_BASE',
  defaultValue: 'http://127.0.0.1:8001',
);
