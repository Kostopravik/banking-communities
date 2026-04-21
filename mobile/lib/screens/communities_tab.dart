import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api.dart';
import '../auth_provider.dart';
import '../models.dart';
import '../theme.dart';
import 'community_detail_screen.dart';

class CommunitiesTab extends StatefulWidget {
  const CommunitiesTab({super.key});

  @override
  State<CommunitiesTab> createState() => _CommunitiesTabState();
}

class _CommunitiesTabState extends State<CommunitiesTab> {
  int _refreshKey = 0;

  String _purchaseWord(int n) {
    final mod10 = n % 10;
    final mod100 = n % 100;
    if (mod10 == 1 && mod100 != 11) return 'покупку';
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'покупки';
    return 'покупок';
  }

  Future<(int, List<CommunityOverview>)> _load(AuthProvider auth) async {
    return auth.api.communitiesOverview();
  }

  Future<void> _join(BuildContext context, AuthProvider auth, CommunityOverview c) async {
    try {
      await auth.api.joinCommunity(c.id);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Вы вступили в «${c.name}»')),
        );
        setState(() => _refreshKey++);
      }
    } on ApiException catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Не удалось: ${e.body}')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return RefreshIndicator(
      onRefresh: () async => setState(() => _refreshKey++),
      child: FutureBuilder<(int, List<CommunityOverview>)>(
        key: ValueKey(_refreshKey),
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
          final list = snap.data!.$2;
          final joined = list.where((c) => c.isMember).toList();
          final available = list
              .where((c) => !c.isMember && c.transactionsNeeded == 0)
              .toList();
          final locked = list
              .where((c) => !c.isMember && c.transactionsNeeded > 0)
              .toList();

          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              sectionTitle('Ваши'),
              ...joined.map(
                (c) => ListTile(
                  leading: CircleAvatar(
                    backgroundColor: vtbBlue.withOpacity(0.12),
                    child: const Icon(Icons.groups, color: vtbBlue),
                  ),
                  title: Text(c.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: c.description != null && c.description!.isNotEmpty
                      ? Text(
                          c.description!,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        )
                      : null,
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute<void>(
                      builder: (_) => CommunityDetailScreen(community: c),
                    ),
                  ),
                ),
              ),
              sectionTitle('Можете вступить'),
              ...available.map(
                (c) => ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Colors.green.withOpacity(0.12),
                    child: const Icon(Icons.group_add, color: Colors.green),
                  ),
                  title: Text(c.name),
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute<void>(
                      builder: (_) => CommunityDetailScreen(community: c),
                    ),
                  ),
                  trailing: ElevatedButton(
                    onPressed: () => _join(context, auth, c),
                    child: const Text('Вступить'),
                  ),
                ),
              ),
              sectionTitle('Недоступные'),
              const Padding(
                padding: EdgeInsets.only(left: 16, right: 16, bottom: 8, top: 4),
                child: Text(
                  'Чтобы получать выгоды и писать посты, сначала вступите в сообщество.',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
              ...locked.map(
                (c) => ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Colors.grey.shade200,
                    child: Icon(Icons.groups, color: Colors.grey.shade600),
                  ),
                  title: Text(c.name),
                  subtitle: Text(
                    'Пока недоступно. Чтобы вступить, нужно еще '
                    '${c.transactionsNeeded} ${_purchaseWord(c.transactionsNeeded)} '
                    'в категории этого сообщества.',
                  ),
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text(
                          'Чтобы получать выгоды и писать посты, сначала вступите в сообщество.',
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
