import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../auth_provider.dart';
import '../theme.dart';
import 'cashback_tab.dart';
import 'communities_tab.dart';
import 'feed_tab.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user!;

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(10),
              ),
              alignment: Alignment.center,
              child: const Text(
                'VTB',
                style: TextStyle(
                  color: vtbBlue,
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(child: Text(user.displayName)),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Выйти',
            icon: const Icon(Icons.logout),
            onPressed: () => auth.logout(),
          ),
        ],
      ),
      body: IndexedStack(
        index: _index,
        children: const [
          FeedTab(),
          CommunitiesTab(),
          CashbackTab(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        selectedItemColor: vtbBlue,
        currentIndex: _index,
        onTap: (i) => setState(() => _index = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Лента'),
          BottomNavigationBarItem(icon: Icon(Icons.group), label: 'Сообщества'),
          BottomNavigationBarItem(icon: Icon(Icons.attach_money), label: 'Кэшбэк'),
        ],
      ),
    );
  }
}
