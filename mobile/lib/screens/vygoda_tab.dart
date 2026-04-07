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

  Future<(List<BenefitDto>, List<CashbackDto>)> _load(
    AuthProvider auth,
  ) async {
    final api = auth.api;
    final benefits = await api.myBenefits();
    final cash = await api.myCashback();
    return (benefits, cash);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return RefreshIndicator(
      onRefresh: () async => setState(() => _key++),
      child: FutureBuilder<(List<BenefitDto>, List<CashbackDto>)>(
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
          final benefits = snap.data!.$1;
          final cash = snap.data!.$2;

          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              sectionTitle('Уже начислено'),
              const SizedBox(height: 8),
              if (cash.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: Text('Пока начислений нет'),
                )
              else
                ...cash.map(_cashCard),
              sectionTitle('Кэшбэки сообществ'),
              if (benefits.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: Text('Пока нет доступных предложений.'),
                )
              else
                ...benefits.map(_benefitCard),
            ],
          );
        },
      ),
    );
  }

  Widget _benefitCard(BenefitDto b) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        title: Text(b.communityName),
        subtitle: Text('${b.title}\n${b.hint}'),
        isThreeLine: true,
        trailing: Text(
          '${b.percent}%',
          style: TextStyle(
            color: b.isActive ? Colors.green : Colors.grey.shade600,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
      ),
    );
  }

  Widget _cashCard(CashbackDto c) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        title: Text(c.categoryLabel ?? 'Партнерский кэшбэк'),
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

}
