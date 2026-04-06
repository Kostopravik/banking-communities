import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api.dart';
import '../auth_provider.dart';
import '../models.dart';
import '../theme.dart';

String _formatWhen(String? iso) {
  if (iso == null || iso.isEmpty) return '';
  try {
    final dt = DateTime.parse(iso).toLocal();
    final d = dt.day.toString().padLeft(2, '0');
    final m = dt.month.toString().padLeft(2, '0');
    final h = dt.hour.toString().padLeft(2, '0');
    final min = dt.minute.toString().padLeft(2, '0');
    return '$d.$m.${dt.year} $h:$min';
  } catch (_) {
    return iso;
  }
}

List<CommentDto> _orderedForDisplay(List<CommentDto> all) {
  final roots = all.where((c) => c.idParent == null).toList();
  final out = <CommentDto>[];
  for (final r in roots) {
    out.add(r);
    out.addAll(all.where((c) => c.idParent == r.id));
  }
  for (final c in all) {
    if (c.idParent != null && !roots.any((x) => x.id == c.idParent)) {
      if (!out.contains(c)) out.add(c);
    }
  }
  return out;
}

class PostCard extends StatefulWidget {
  const PostCard({
    super.key,
    required this.post,
    required this.communityName,
    this.onChanged,
  });

  final PostDto post;
  final String communityName;
  final VoidCallback? onChanged;

  @override
  State<PostCard> createState() => _PostCardState();
}

class _PostCardState extends State<PostCard> {
  final TextEditingController _controller = TextEditingController();
  bool _showComments = false;
  late int _likeCount;
  late bool _liked;
  List<CommentDto> _comments = [];
  bool _loadingComments = false;
  bool _sending = false;
  int? _replyToId;
  String? _replyToName;

  @override
  void initState() {
    super.initState();
    _likeCount = widget.post.likeCount;
    _liked = widget.post.likedByMe;
  }

  @override
  void didUpdateWidget(PostCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.post.id != widget.post.id) {
      _likeCount = widget.post.likeCount;
      _liked = widget.post.likedByMe;
      _comments = [];
      _showComments = false;
      _replyToId = null;
      _replyToName = null;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _openComments(ApiClient api) async {
    final willShow = !_showComments;
    setState(() => _showComments = willShow);
    if (!willShow) return;
    setState(() => _loadingComments = true);
    try {
      final list = await api.postComments(widget.post.id);
      if (mounted) {
        setState(() {
          _comments = list;
          _loadingComments = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loadingComments = false);
    }
  }

  Future<void> _toggleLike(ApiClient api) async {
    try {
      final r = await api.togglePostLike(widget.post.id);
      if (mounted) {
        setState(() {
          _liked = r.liked;
          _likeCount = r.likeCount;
        });
        widget.onChanged?.call();
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Лайк: ${e.body}')),
        );
      }
    }
  }

  Future<void> _sendComment(ApiClient api) async {
    final text = _controller.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() => _sending = true);
    try {
      final c = await api.addPostComment(
        widget.post.id,
        text,
        parentId: _replyToId,
      );
      if (mounted) {
        setState(() {
          _comments = [..._comments, c];
          _controller.clear();
          _replyToId = null;
          _replyToName = null;
        });
      }
      widget.onChanged?.call();
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.body)),
        );
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final api = context.read<AuthProvider>().api;
    final title = widget.post.title ?? '';
    final body = widget.post.text ?? '';

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      elevation: 2,
      shadowColor: Colors.black26,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: vtbBlue.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    widget.communityName,
                    style: const TextStyle(
                      color: vtbBlue,
                      fontWeight: FontWeight.w700,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            if (title.isNotEmpty)
              Text(
                title,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
            if (title.isNotEmpty) const SizedBox(height: 8),
            if (body.isNotEmpty)
              Text(
                body,
                style: TextStyle(fontSize: 15, height: 1.35, color: Colors.grey[850]),
              ),
            const SizedBox(height: 12),
            Row(
              children: [
                Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: () => _toggleLike(api),
                    borderRadius: BorderRadius.circular(24),
                    child: Padding(
                      padding: const EdgeInsets.all(8),
                      child: Row(
                        children: [
                          Icon(
                            Icons.favorite,
                            size: 26,
                            color: _liked ? Colors.red : Colors.grey.shade400,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            '$_likeCount',
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              color: _liked ? Colors.red.shade700 : Colors.grey.shade700,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const Spacer(),
                TextButton.icon(
                  onPressed: () => _openComments(api),
                  icon: Icon(_showComments ? Icons.expand_less : Icons.chat_bubble_outline,
                      color: vtbBlue, size: 20),
                  label: Text(_showComments ? 'Скрыть' : 'Комментарии'),
                  style: TextButton.styleFrom(foregroundColor: vtbBlue),
                ),
              ],
            ),
            if (_showComments) ...[
              const Divider(height: 24),
              if (_loadingComments)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(12),
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                )
              else
                ..._orderedForDisplay(_comments).map((c) => _commentBlock(c, api)),
              if (_replyToId != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: InputChip(
                    label: Text('Ответ для $_replyToName'),
                    deleteIcon: const Icon(Icons.close, size: 18),
                    onDeleted: () => setState(() {
                      _replyToId = null;
                      _replyToName = null;
                    }),
                  ),
                ),
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      decoration: InputDecoration(
                        hintText: _replyToId != null
                            ? 'Ваш ответ…'
                            : 'Написать комментарий',
                        filled: true,
                        fillColor: Colors.grey.shade50,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(color: Colors.grey.shade300),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(color: Colors.grey.shade300),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: const BorderSide(color: vtbBlue, width: 1.5),
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 12,
                        ),
                      ),
                      minLines: 1,
                      maxLines: 4,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Material(
                    color: vtbBlue,
                    borderRadius: BorderRadius.circular(14),
                    child: InkWell(
                      onTap: _sending ? null : () => _sendComment(api),
                      borderRadius: BorderRadius.circular(14),
                      child: SizedBox(
                        width: 48,
                        height: 48,
                        child: Center(
                          child: _sending
                              ? const SizedBox(
                                  width: 22,
                                  height: 22,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Icon(Icons.send, color: Colors.white),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _commentBlock(CommentDto c, ApiClient api) {
    final isReply = c.idParent != null;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: EdgeInsets.only(
        left: isReply ? 16 : 0,
        top: 8,
        bottom: 8,
        right: 8,
      ),
      decoration: BoxDecoration(
        border: Border(
          left: isReply
              ? const BorderSide(color: vtbBlue, width: 3)
              : BorderSide.none,
        ),
        color: isReply ? Colors.blue.shade50.withOpacity(0.5) : Colors.grey.shade50,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (isReply && (c.replyToName ?? '').isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text(
                '↳ ответ ${c.replyToName}',
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.blueGrey.shade700,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      c.senderName,
                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                    ),
                    Text(
                      _formatWhen(c.createdAt),
                      style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                    ),
                    const SizedBox(height: 4),
                    Text(c.message, style: const TextStyle(fontSize: 14)),
                  ],
                ),
              ),
              TextButton(
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                onPressed: () => setState(() {
                  _replyToId = c.id;
                  _replyToName = c.senderName;
                }),
                child: const Text('Ответить', style: TextStyle(fontSize: 12)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
