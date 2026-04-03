import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../auth_provider.dart';
import '../models.dart';
import '../theme.dart';

class CashbackTab extends StatefulWidget {
  const CashbackTab({super.key});

  @override
  State<CashbackTab> createState() => _CashbackTabState();
}

class _CashbackTabState extends State<CashbackTab> {
  int _key = 0;

  Future<(List<CashbackDto>, List<RecommendItem>)> _load(AuthProvider auth) async {
    final api = auth.api;
    final cash = await api.myCashback();
    final rec = await api.recommendMe();
    return (cash, rec);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return RefreshIndicator(
      onRefresh: () async => setState(() => _key++),
      child: FutureBuilder<(List<CashbackDto>, List<RecommendItem>)>(
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
          final cash = snap.data!.$1;
          final rec = snap.data!.$2;

          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              sectionTitle('Ваш кэшбэк (из БД)'),
              if (cash.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: Text('Пока нет начислений'),
                )
              else
                ...cash.map(_cashCard),
              sectionTitle('Персональные предложения (Neo4j)'),
              if (rec.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: Text('Нет рекомендаций (мало транзакций в графе)'),
                )
              else
                ...rec.map(_recCard),
            ],
          );
        },
      ),
    );
  }

  Widget _cashCard(CashbackDto c) {
    return Card(
      margin: const EdgeInsets.all(8),
      child: ListTile(
        title: Text('MCC ${c.place}'),
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
      margin: const EdgeInsets.all(8),
      child: ListTile(
        title: Text(r.placeName),
        subtitle: Text('${r.category} · операций: ${r.txCount}, сумма: ${r.totalAmount.toStringAsFixed(0)} ₽'),
        trailing: const Icon(Icons.store, color: vtbBlue),
      ),
    );
  }
}
