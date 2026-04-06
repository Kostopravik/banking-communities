import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../auth_provider.dart';
import '../models.dart';
import '../theme.dart';

class VygodTab extends StatefulWidget {
  const VygodTab({super.key});

  @override
  State<VygodTab> createState() => _VygodTabState();
}

class _VygodTabState extends State<VygodTab> {
  int _key = 0;

  Future<(List<CashbackOpportunityDto>, List<RecommendItem>, List<CashbackDto>)> _load(
    AuthProvider auth,
  ) async {
    final api = auth.api;
    final opps = await api.cashbackOpportunities();
    final rec = await api.recommendMe();
    final cash = await api.myCashback();
    return (opps, rec, cash);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return RefreshIndicator(
      onRefresh: () async => setState(() => _key++),
      child: FutureBuilder<(List<CashbackOpportunityDto>, List<RecommendItem>, List<CashbackDto>)>(
        key: ValueKey(_key),
        future: _load(auth),
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text('Ошибка: ${snap.error}'),
                ),
              ],
            );
          }
          final opps = snap.data!.$1;
          final rec = snap.data!.$2;
          final cash = snap.data!.$3;
          final unlocked = opps.where((o) => o.eligible).toList();
          final locked = opps.where((o) => !o.eligible).toList();

          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              _infoCard(
                title: 'Как устроено',
                body:
                    'Приложение на Flutter ходит только в FastAPI. Neo4j и PostgreSQL '
                    'на сервере; прямого доступа из Dart к графу нет.\n\n'
                    '• Кэшбэки по MCC — из PostgreSQL, «открываются», когда в Neo4j '
                    '≥3 отдельных операции в той же MCC-категории.\n'
                    '• Начисленный кэшбэк — записи из БД (симуляция уже зачисленного).\n'
                    '• Рекомендации по тратам — из Neo4j: магазины, куда вы '
                    'часто ходите (≥3 покупок = ≥3 рёбер в графе), чтобы предложить акции.',
              ),
              sectionTitle('Кэшбэки по MCC (≥3 операций в категории)'),
              if (unlocked.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: Text('Пока нет категорий с 3+ операциями по данным графа.'),
                )
              else
                ...unlocked.map(_oppUnlockedCard),
              sectionTitle('Пока недоступны (мало операций в категории)'),
              ...locked.map((o) => _oppLockedCard(context, o)),
              sectionTitle('Начисленный кэшбэк (уже в вашей истории)'),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Text(
                  'Это не «следующая трата после вступления», а тестовые строки в БД: '
                  'связь client ↔ cashback. В продукте сюда попадали бы реальные начисления.',
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
                ),
              ),
              const SizedBox(height: 8),
              if (cash.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: Text('Нет записей client_cashback'),
                )
              else
                ...cash.map(_cashCard),
              sectionTitle('Рекомендации по тратам (Neo4j)'),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Text(
                  'Для чего: подсказать персональные предложения по местам, '
                  'куда вы уже много платите (частые отдельные покупки в графе).',
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
                ),
              ),
              const SizedBox(height: 4),
              if (rec.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: Text('Нет мест с ≥3 отдельными операциями'),
                )
              else
                ...rec.map(_recCard),
            ],
          );
        },
      ),
    );
  }

  Widget _infoCard({required String title, required String body}) {
    return Card(
      margin: const EdgeInsets.fromLTRB(12, 12, 12, 8),
      elevation: 0,
      color: Colors.blue.shade50,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            const SizedBox(height: 8),
            Text(body, style: TextStyle(fontSize: 13, height: 1.4, color: Colors.grey.shade900)),
          ],
        ),
      ),
    );
  }

  Widget _oppUnlockedCard(CashbackOpportunityDto o) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        title: Text(o.categoryLabel ?? 'MCC ${o.placeMcc}'),
        subtitle: Text(
          'Операций в категории: ${o.operationsInCategory}/${o.operationsRequired}. '
          '${o.accrued ? "Начисление есть" : "Начисление не привязано (MVP)"}',
        ),
        trailing: Text(
          '${o.amount.toStringAsFixed(0)} ₽',
          style: const TextStyle(
            color: Colors.green,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
      ),
    );
  }

  Widget _oppLockedCard(BuildContext context, CashbackOpportunityDto o) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        title: Text(o.categoryLabel ?? 'MCC ${o.placeMcc}'),
        subtitle: Text(
          '${o.operationsInCategory}/${o.operationsRequired} операций в категории',
        ),
        trailing: const Icon(Icons.lock_outline, color: Colors.grey),
        onTap: () {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(o.hint), duration: const Duration(seconds: 5)),
          );
        },
      ),
    );
  }

  Widget _cashCard(CashbackDto c) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        title: Text(c.categoryLabel ?? 'MCC ${c.place}'),
        subtitle: Text(c.createdAt ?? ''),
        trailing: Text(
          '${c.amount.toStringAsFixed(0)} ₽',
          style: const TextStyle(
            color: Colors.green,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget _recCard(RecommendItem r) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        title: Text(r.placeName),
        subtitle: Text(
          '${r.category} · отдельных операций: ${r.operationCount}, '
          'сумма: ${r.totalAmount.toStringAsFixed(0)} ₽',
        ),
        trailing: const Icon(Icons.store, color: vtbBlue),
      ),
    );
  }
}
