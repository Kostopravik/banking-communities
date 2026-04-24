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

          final activeBenefits = benefits.where((b) => b.isActive).toList();
          final inactiveBenefits = benefits.where((b) => !b.isActive).toList();

          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              // === СЕКЦИЯ 1: Уже начислено ===
              sectionTitle('Уже начислено'),
              const SizedBox(height: 8),
              if (cash.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: Text('Пока начислений нет'),
                )
              else
                ...cash.map(_cashCard),
              
              const SizedBox(height: 16),
              
              // === СЕКЦИЯ 2: Доступный кэшбэк сообществ ===
              if (activeBenefits.isNotEmpty) ...[
                sectionTitle('Доступные предложения'),
                ...activeBenefits.map(_benefitCard),
              ],
              
              const SizedBox(height: 16),
              
              // === СЕКЦИЯ 3: Кэшбэк сообществ с условиями ===
              if (inactiveBenefits.isNotEmpty) ...[
                sectionTitle('Предложения с условиями'),
                const Padding(
                  padding: EdgeInsets.only(left: 16, right: 16, bottom: 8, top: 4),
                  child: Text(
                    'Выполните условия, чтобы открыть доступ',
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.grey,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ),
                ...inactiveBenefits.map(_benefitCard),
              ],
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
        leading: CircleAvatar(
          backgroundColor: b.isActive 
              ? Colors.green.withOpacity(0.12) 
              : Colors.grey.shade200,
          child: Icon(
            b.isActive ? Icons.card_giftcard : Icons.workspace_premium,
            color: b.isActive ? Colors.green : Colors.grey.shade600,
          ),
        ),
        title: Text(b.communityName),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${b.title}'),
            Text(
              b.hint,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey.shade600,
              ),
            ),
          ],
        ),
        isThreeLine: true,
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '${b.percent}%',
              style: TextStyle(
                color: b.isActive ? Colors.green : Colors.grey.shade600,
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),
            if (!b.isActive && b.operationsNeededToJoin > 0)
              Text(
                '${b.operationsNeededToJoin} покуп.',
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.grey.shade600,
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _cashCard(CashbackDto c) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: Colors.green.withOpacity(0.12),
          child: const Icon(Icons.payments, color: Colors.green),
        ),
        title: Text(c.categoryLabel ?? 'Кэшбэк'),
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