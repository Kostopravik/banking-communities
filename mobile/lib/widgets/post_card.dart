import 'package:flutter/material.dart';

import '../models.dart';
import '../theme.dart';

class PostCard extends StatefulWidget {
  const PostCard({
    super.key,
    required this.post,
    required this.communityName,
  });

  final PostDto post;
  final String communityName;

  @override
  State<PostCard> createState() => _PostCardState();
}

class _PostCardState extends State<PostCard> {
  final TextEditingController _controller = TextEditingController();
  bool _showComments = false;
  late int _likes;
  final List<String> _comments = [];

  @override
  void initState() {
    super.initState();
    _likes = widget.post.rating;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.post.title ?? '';
    final body = widget.post.text ?? '';

    return Container(
      margin: const EdgeInsets.all(10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 6)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '📍 ${widget.communityName}',
            style: const TextStyle(color: vtbBlue, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          if (title.isNotEmpty)
            Text(
              title,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          if (title.isNotEmpty) const SizedBox(height: 6),
          if (body.isNotEmpty) Text(body),
          const SizedBox(height: 10),
          Row(
            children: [
              IconButton(
                icon: const Icon(Icons.favorite, color: Colors.red),
                onPressed: () => setState(() => _likes++),
              ),
              Text('$_likes'),
              const Spacer(),
              TextButton(
                onPressed: () => setState(() => _showComments = !_showComments),
                child: const Text('Комментарии'),
              ),
            ],
          ),
          if (_showComments) ...[
            const Divider(),
            ..._comments.map(
              (c) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Text('💬 $c'),
              ),
            ),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(hintText: 'Написать комментарий'),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send, color: vtbBlue),
                  onPressed: () {
                    if (_controller.text.isEmpty) return;
                    setState(() {
                      _comments.add(_controller.text);
                      _controller.clear();
                    });
                  },
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
