import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../auth_provider.dart';
import '../models.dart';
import '../theme.dart';
import '../widgets/post_card.dart';

class FeedTab extends StatefulWidget {
  const FeedTab({super.key});

  @override
  State<FeedTab> createState() => _FeedTabState();
}

class _FeedTabState extends State<FeedTab> {
  int _refreshKey = 0;

  Future<_FeedData> _load(AuthProvider auth) async {
    final api = auth.api;
    final (_, overview) = await api.communitiesOverview();
    final joined = overview.where((c) => c.isMember).map((c) => c.id).toSet();
    final names = {for (final c in overview) c.id: c.name};
    final allPosts = await api.posts();
    final feed = allPosts.where((p) => joined.contains(p.idCommunity)).toList();
    return _FeedData(posts: feed, names: names);
  }

  Future<void> _onRefresh(AuthProvider auth) async {
    setState(() => _refreshKey++);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return RefreshIndicator(
      onRefresh: () async {
        setState(() => _refreshKey++);
      },
      child: FutureBuilder<_FeedData>(
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
          final data = snap.data!;
          if (data.posts.isEmpty) {
            return ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              children: const [
                SizedBox(height: 80),
                Center(
                  child: Text(
                    'Нет постов из ваших сообществ.\nВступите в сообщества во вкладке «Сообщества».',
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            );
          }
          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              sectionTitle('Лента'),
              ...data.posts.map(
                (p) => PostCard(
                  post: p,
                  communityName: data.names[p.idCommunity] ?? 'Сообщество ${p.idCommunity}',
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _FeedData {
  _FeedData({required this.posts, required this.names});

  final List<PostDto> posts;
  final Map<int, String> names;
}
