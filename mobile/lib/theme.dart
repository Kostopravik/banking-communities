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
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: vtbBlue,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
    scaffoldBackgroundColor: Colors.grey[100],
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
