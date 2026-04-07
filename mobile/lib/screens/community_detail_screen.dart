import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../auth_provider.dart';
import '../models.dart';
import '../theme.dart';
import '../widgets/post_card.dart';
import 'compose_post_screen.dart';

class CommunityDetailScreen extends StatefulWidget {
  const CommunityDetailScreen({super.key, required this.community});

  final CommunityOverview community;

  @override
  State<CommunityDetailScreen> createState() => _CommunityDetailScreenState();
}

class _CommunityDetailScreenState extends State<CommunityDetailScreen> {
  int _refreshKey = 0;

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;

    return Scaffold(
      appBar: AppBar(title: Text(widget.community.name)),
      floatingActionButton: widget.community.isMember
          ? FloatingActionButton.extended(
              onPressed: () async {
                final ok = await Navigator.push<bool>(
                  context,
                  MaterialPageRoute<bool>(
                    builder: (_) => ComposePostScreen(community: widget.community),
                  ),
                );
                if (ok == true && mounted) setState(() => _refreshKey++);
              },
              backgroundColor: vtbBlue,
              icon: const Icon(Icons.edit_note),
              label: const Text('Написать пост'),
            )
          : null,
      body: FutureBuilder<List<PostDto>>(
        key: ValueKey(_refreshKey),
        future: api.posts(communityId: widget.community.id),
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text('Ошибка: ${snap.error}'));
          }
          final list = snap.data ?? [];
          if (list.isEmpty) {
            return ListView(
              padding: const EdgeInsets.all(24),
              children: [
                if (!widget.community.isMember)
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(
                        'Вступите в сообщество, чтобы писать посты.',
                        style: TextStyle(color: Colors.grey.shade700),
                      ),
                    ),
                  )
                else
                  const Padding(
                    padding: EdgeInsets.all(12),
                    child: Text(
                      'Пока нет постов - нажмите «Написать пост».',
                      textAlign: TextAlign.center,
                    ),
                  ),
              ],
            );
          }
          return ListView(
            padding: const EdgeInsets.only(bottom: 88),
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                child: Text(
                  'Посты сообщества',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey.shade900,
                  ),
                ),
              ),
              ...list.map(
                (p) => PostCard(
                  post: p,
                  communityName: widget.community.name,
                  onChanged: () => setState(() => _refreshKey++),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
