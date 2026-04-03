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
              ...locked.map(
                (c) => ListTile(
                  title: Text(c.name),
                  subtitle: Text('Нужно ещё ${c.transactionsNeeded} транзакций (по Neo4j)'),
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute<void>(
                      builder: (_) => CommunityDetailScreen(community: c),
                    ),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
