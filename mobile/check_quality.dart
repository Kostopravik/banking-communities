import 'dart:io';

void main() async {
  print('=== Flutter Project Quality Report ===\n');
  
  final libDir = Directory('lib');
  if (!await libDir.exists()) {
    print('❌ Папка lib не найдена!');
    print('📁 Текущая папка: ${Directory.current.path}');
    return;
  }
  
  var fileCount = 0;
  var totalLines = 0;
  
  await for (final entity in libDir.list(recursive: true)) {
    if (entity is File && entity.path.endsWith('.dart')) {
      fileCount++;
      final lines = await entity.readAsLines();
      totalLines += lines.length;
    }
  }
  
  print('📁 Dart файлов: ${fileCount}');
  print('📝 Строк кода: ~${totalLines}');
  
  final testDir = Directory('test');
  if (await testDir.exists()) {
    var testCount = 0;
    await for (final entity in testDir.list(recursive: true)) {
      if (entity is File && entity.path.endsWith('_test.dart')) {
        testCount++;
      }
    }
    print('🧪 Тестов: ${testCount}');
  } else {
    print('🧪 Тестов: 0');
  }
  
  print('\n✅ Отчет готов!');
}