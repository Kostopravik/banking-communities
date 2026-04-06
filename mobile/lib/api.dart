import 'dart:convert';

import 'package:http/http.dart' as http;

import 'config.dart';
import 'models.dart';

class ApiException implements Exception {
  ApiException(this.statusCode, this.body);
  final int statusCode;
  final String body;
  @override
  String toString() => 'HTTP $statusCode: $body';
}

class ApiClient {
  ApiClient({this.baseUrl = kApiBase});

  final String baseUrl;
  String? token;

  Map<String, String> _headers({bool jsonBody = false}) {
    return <String, String>{
      if (jsonBody) 'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Future<(UserPublic, String)> login({
    required String login,
    required String password,
  }) async {
    final r = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: _headers(jsonBody: true),
      body: jsonEncode({'login': login, 'password': password}),
    );
    if (r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    final map = jsonDecode(r.body) as Map<String, dynamic>;
    final u = UserPublic.fromJson(map['user'] as Map<String, dynamic>);
    final tok = map['access_token'] as String;
    return (u, tok);
  }

  Future<UserPublic> me() async {
    final r = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: _headers(),
    );
    if (r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    return UserPublic.fromJson(
      jsonDecode(r.body) as Map<String, dynamic>,
    );
  }

  Future<(int, List<CommunityOverview>)> communitiesOverview() async {
    final r = await http.get(
      Uri.parse('$baseUrl/communities/overview'),
      headers: _headers(),
    );
    if (r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    final map = jsonDecode(r.body) as Map<String, dynamic>;
    final rawTotal = map['total_operations'] ?? map['total_tx_count'];
    final total = (rawTotal as num).toInt();
    final list = (map['communities'] as List<dynamic>)
        .map((e) => CommunityOverview.fromJson(e as Map<String, dynamic>))
        .toList();
    return (total, list);
  }

  Future<PostDto> createPost({
    required int communityId,
    required String title,
    required String text,
  }) async {
    final r = await http.post(
      Uri.parse('$baseUrl/posts'),
      headers: _headers(jsonBody: true),
      body: jsonEncode({
        'id_community': communityId,
        'title': title,
        'text': text,
      }),
    );
    if (r.statusCode != 201 && r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    return PostDto.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
  }

  Future<List<PostDto>> posts({int? communityId}) async {
    final uri = communityId == null
        ? Uri.parse('$baseUrl/posts')
        : Uri.parse('$baseUrl/posts').replace(
            queryParameters: {'community_id': '$communityId'},
          );
    final r = await http.get(uri, headers: _headers());
    if (r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    final list = jsonDecode(r.body) as List<dynamic>;
    return list
        .map((e) => PostDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> joinCommunity(int communityId) async {
    final r = await http.post(
      Uri.parse('$baseUrl/communities/$communityId/join'),
      headers: _headers(),
    );
    if (r.statusCode != 204 && r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
  }

  Future<List<CashbackOpportunityDto>> cashbackOpportunities() async {
    final r = await http.get(
      Uri.parse('$baseUrl/users/me/cashback-opportunities'),
      headers: _headers(),
    );
    if (r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    final list = jsonDecode(r.body) as List<dynamic>;
    return list
        .map((e) => CashbackOpportunityDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<CashbackDto>> myCashback() async {
    final r = await http.get(
      Uri.parse('$baseUrl/users/me/cashback'),
      headers: _headers(),
    );
    if (r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    final list = jsonDecode(r.body) as List<dynamic>;
    return list
        .map((e) => CashbackDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<BenefitDto>> myBenefits() async {
    final r = await http.get(
      Uri.parse('$baseUrl/users/me/benefits'),
      headers: _headers(),
    );
    if (r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    final list = jsonDecode(r.body) as List<dynamic>;
    return list
        .map((e) => BenefitDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<RecommendItem>> recommendMe() async {
    final r = await http.get(
      Uri.parse('$baseUrl/recommend/me'),
      headers: _headers(),
    );
    if (r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    final map = jsonDecode(r.body) as Map<String, dynamic>;
    final list = map['recommendations'] as List<dynamic>? ?? [];
    return list
        .map((e) => RecommendItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<({bool liked, int likeCount})> togglePostLike(int postId) async {
    final r = await http.post(
      Uri.parse('$baseUrl/posts/$postId/like'),
      headers: _headers(),
    );
    if (r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    final map = jsonDecode(r.body) as Map<String, dynamic>;
    return (
      liked: map['liked'] as bool,
      likeCount: (map['like_count'] as num).toInt(),
    );
  }

  Future<List<CommentDto>> postComments(int postId) async {
    final r = await http.get(
      Uri.parse('$baseUrl/posts/$postId/comments'),
      headers: _headers(),
    );
    if (r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    final list = jsonDecode(r.body) as List<dynamic>;
    return list
        .map((e) => CommentDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CommentDto> addPostComment(
    int postId,
    String message, {
    int? parentId,
  }) async {
    final body = <String, dynamic>{'message': message};
    if (parentId != null) body['parent_id'] = parentId;
    final r = await http.post(
      Uri.parse('$baseUrl/posts/$postId/comments'),
      headers: _headers(jsonBody: true),
      body: jsonEncode(body),
    );
    if (r.statusCode != 201 && r.statusCode != 200) {
      throw ApiException(r.statusCode, r.body);
    }
    return CommentDto.fromJson(
      jsonDecode(r.body) as Map<String, dynamic>,
    );
  }
}
