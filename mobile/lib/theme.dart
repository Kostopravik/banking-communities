import 'package:flutter/material.dart';

const Color vtbBlue = Color(0xFF005BFF);

ThemeData buildVtbTheme() {
  return ThemeData(
    colorScheme: ColorScheme.fromSeed(seedColor: vtbBlue, brightness: Brightness.light),
    primaryColor: vtbBlue,
    useMaterial3: true,
    appBarTheme: const AppBarTheme(
      backgroundColor: vtbBlue,
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        color: Colors.white,
        fontSize: 18,
        fontWeight: FontWeight.w600,
      ),
    ),
    cardTheme: CardThemeData(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: vtbBlue,
        foregroundColor: Colors.white,
        elevation: 1,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      selectedItemColor: vtbBlue,
      unselectedItemColor: Colors.grey,
      type: BottomNavigationBarType.fixed,
    ),
    scaffoldBackgroundColor: const Color(0xFFF0F2F7),
  );
}

Widget sectionTitle(String text) {
  return Padding(
    padding: const EdgeInsets.all(10),
    child: Text(
      text,
      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
    ),
  );
}
