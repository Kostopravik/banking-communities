import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../auth_provider.dart';
import '../models.dart';
import '../widgets/post_card.dart';

class CommunityDetailScreen extends StatelessWidget {
  const CommunityDetailScreen({super.key, required this.community});

  final CommunityOverview community;

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;

    return Scaffold(
      appBar: AppBar(title: Text(community.name)),
      body: FutureBuilder<List<PostDto>>(
        future: api.posts(communityId: community.id),
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Text('Ошибка: ${snap.error}'));
          }
          final list = snap.data ?? [];
          if (list.isEmpty) {
            return const Padding(
              padding: EdgeInsets.all(12),
              child: Text('Пока нет постов'),
            );
          }
          return ListView(
            children: [
              const Padding(
                padding: EdgeInsets.all(12),
                child: Text(
                  'Посты сообщества',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
              ),
              ...list.map(
                (p) => PostCard(
                  post: p,
                  communityName: community.name,
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
