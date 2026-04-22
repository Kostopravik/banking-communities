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

  Future<(List<BenefitDto>, List<CashbackDto>, List<CashbackOpportunityDto>)> _load(
    AuthProvider auth,
  ) async {
    final api = auth.api;
    final benefits = await api.myBenefits();
    final cash = await api.myCashback();
    final opportunities = await api.cashbackOpportunities();
    return (benefits, cash, opportunities);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return RefreshIndicator(
      onRefresh: () async => setState(() => _key++),
      child: FutureBuilder<(List<BenefitDto>, List<CashbackDto>, List<CashbackOpportunityDto>)>(
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
          final opportunities = snap.data!.$3;

          // Разделяем на активные/доступные (зелёные) и неактивные/недоступные (серые)
          final activeBenefits = benefits.where((b) => b.isActive).toList();
          final inactiveBenefits = benefits.where((b) => !b.isActive).toList();
          
          final availableOpportunities = opportunities.where((o) => o.eligible).toList()
            ..sort((a, b) => a.id.compareTo(b.id));
          final unavailableOpportunities = opportunities.where((o) => !o.eligible).toList()
            ..sort((a, b) => a.id.compareTo(b.id));

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
              
              // === СЕКЦИЯ 2: ВСЕ ДОСТУПНЫЕ ПРЕДЛОЖЕНИЯ (зелёные) ===
              if (activeBenefits.isNotEmpty || availableOpportunities.isNotEmpty) ...[
                sectionTitle('Доступные предложения'),
                
                // Активные кэшбэки сообществ (с процентами)
                if (activeBenefits.isNotEmpty) ...[
                  const Padding(
                    padding: EdgeInsets.only(left: 16, right: 16, top: 8, bottom: 4),
                    child: Text(
                      'Кэшбэк сообществ',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Colors.green,
                      ),
                    ),
                  ),
                  ...activeBenefits.map(_benefitCard),
                ],
                
                // Доступные кэшбэки из каталога
                if (availableOpportunities.isNotEmpty) ...[
                  const Padding(
                    padding: EdgeInsets.only(left: 16, right: 16, top: 8, bottom: 4),
                    child: Text(
                      'Партнёрский кэшбэк',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Colors.green,
                      ),
                    ),
                  ),
                  ...availableOpportunities.map(_opportunityCard),
                ],
              ],
              
              const SizedBox(height: 16),
              
              // === СЕКЦИЯ 3: ВСЕ НЕДОСТУПНЫЕ ПРЕДЛОЖЕНИЯ (серые) ===
              if (inactiveBenefits.isNotEmpty || unavailableOpportunities.isNotEmpty) ...[
                sectionTitle('Недоступные предложения'),
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
                
                // Неактивные кэшбэки сообществ
                if (inactiveBenefits.isNotEmpty) ...[
                  const Padding(
                    padding: EdgeInsets.only(left: 16, right: 16, top: 8, bottom: 4),
                    child: Text(
                      'Кэшбэк сообществ',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey,
                      ),
                    ),
                  ),
                  ...inactiveBenefits.map(_benefitCard),
                ],
                
                // Недоступные кэшбэки из каталога
                if (unavailableOpportunities.isNotEmpty) ...[
                  const Padding(
                    padding: EdgeInsets.only(left: 16, right: 16, top: 8, bottom: 4),
                    child: Text(
                      'Партнёрский кэшбэк',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey,
                      ),
                    ),
                  ),
                  ...unavailableOpportunities.map(_opportunityCard),
                ],
              ],
            ],
          );
        },
      ),
    );
  }

  Widget _opportunityCard(CashbackOpportunityDto o) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: o.eligible 
              ? Colors.green.withOpacity(0.12) 
              : Colors.grey.shade200,
          child: Icon(
            o.eligible ? Icons.check_circle : Icons.local_offer,
            color: o.eligible ? Colors.green : Colors.grey.shade600,
          ),
        ),
        title: Text(o.categoryLabel ?? 'Категория ${o.categoryKey}'),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(o.hint),
            if (!o.eligible)
              Text(
                'Прогресс: ${o.operationsInCategory}/${o.operationsRequired} покупок',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade600,
                ),
              ),
          ],
        ),
        isThreeLine: !o.eligible,
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            if (o.accrued)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.green.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.check_circle,
                      size: 14,
                      color: Colors.green,
                    ),
                    SizedBox(width: 4),
                    Text(
                      'Начислен',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.green,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              )
            else if (o.eligible)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: vtbBlue.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  'Доступен',
                  style: TextStyle(
                    fontSize: 12,
                    color: vtbBlue,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              )
            else
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.grey.shade200,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  'Недоступен',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade600,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
          ],
        ),
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