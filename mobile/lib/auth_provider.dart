import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api.dart';
import 'models.dart';

const _kTokenKey = 'access_token';

class AuthProvider extends ChangeNotifier {
  AuthProvider() : _api = ApiClient();

  final ApiClient _api;
  ApiClient get api => _api;

  String? _token;
  UserPublic? _user;
  bool _ready = false;

  String? get token => _token;
  UserPublic? get user => _user;
  bool get isAuthenticated => _token != null && _user != null;
  bool get ready => _ready;

  Future<void> bootstrap() async {
    final prefs = await SharedPreferences.getInstance();
    final t = prefs.getString(_kTokenKey);
    if (t == null || t.isEmpty) {
      _ready = true;
      notifyListeners();
      return;
    }
    _api.token = t;
    try {
      _user = await _api.me();
      _token = t;
    } catch (_) {
      _token = null;
      _user = null;
      _api.token = null;
      await prefs.remove(_kTokenKey);
    }
    _ready = true;
    notifyListeners();
  }

  Future<void> login(String login, String password) async {
    final (u, tok) = await _api.login(login: login, password: password);
    _api.token = tok;
    _token = tok;
    _user = u;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kTokenKey, tok);
    notifyListeners();
  }

  Future<void> logout() async {
    _api.token = null;
    _token = null;
    _user = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kTokenKey);
    notifyListeners();
  }
}
