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
  List<PostDto>? _cachedPosts;

  @override
  void initState() {
    super.initState();
    // Предзагрузка данных для плавного появления
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadPosts();
    });
  }

  Future<void> _loadPosts() async {
    final api = context.read<AuthProvider>().api;
    try {
      final posts = await api.posts(communityId: widget.community.id);
      if (mounted) {
        setState(() {
          _cachedPosts = posts;
        });
      }
    } catch (_) {
      // Ошибка будет показана в билдере
    }
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.community.name,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
        ),
        backgroundColor: vtbBlue,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      floatingActionButton: widget.community.isMember
          ? FloatingActionButton.extended(
              onPressed: () async {
                final ok = await Navigator.push<bool>(
                  context,
                  MaterialPageRoute<bool>(
                    builder: (_) => ComposePostScreen(community: widget.community),
                  ),
                );
                if (ok == true && mounted) {
                  setState(() {
                    _cachedPosts = null;
                    _refreshKey++;
                  });
                  _loadPosts();
                }
              },
              backgroundColor: vtbBlue,
              icon: const Icon(Icons.edit_note, color: Colors.white,),
              label: const Text(
                'Написать пост',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,)
                ),
            )
          : null,
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    // Если есть кэшированные посты - показываем их сразу
    if (_cachedPosts != null) {
      return _buildPostsList(_cachedPosts!);
    }

    // Иначе показываем FutureBuilder
    return FutureBuilder<List<PostDto>>(
      key: ValueKey(_refreshKey),
      future: context.read<AuthProvider>().api.posts(communityId: widget.community.id),
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return _buildLoadingState();
        }
        if (snap.hasError) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'Ошибка: ${snap.error}',
                style: const TextStyle(fontSize: 16),
              ),
            ),
          );
        }
        
        final list = snap.data ?? [];
        // Кэшируем для будущих обновлений
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) {
            setState(() {
              _cachedPosts = list;
            });
          }
        });
        
        return _buildPostsList(list);
      },
    );
  }

  Widget _buildLoadingState() {
    return ListView(
      padding: const EdgeInsets.only(top: 20),
      children: [
        // Показываем скелетоны вместо спиннера
        ...List.generate(3, (_) => _PostSkeleton()),
      ],
    );
  }

  Widget _buildPostsList(List<PostDto> list) {
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
            onChanged: () {
              setState(() {
                _cachedPosts = null;
                _refreshKey++;
              });
              _loadPosts();
            },
          ),
        ),
      ],
    );
  }
}

class _PostSkeleton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 60,
                  height: 32,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                const Spacer(),
                Container(
                  width: 120,  // Увеличим ширину для счетчика
                  height: 32,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              height: 20,
              decoration: BoxDecoration(
                color: Colors.grey.shade300,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              height: 60,
              decoration: BoxDecoration(
                color: Colors.grey.shade200,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Container(
                  width: 60,
                  height: 32,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                const Spacer(),
                Container(
                  width: 100,
                  height: 32,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}