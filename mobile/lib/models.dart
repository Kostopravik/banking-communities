class UserPublic {
  UserPublic({
    required this.id,
    required this.firstName,
    required this.lastName,
    required this.login,
  });

  final int id;
  final String? firstName;
  final String? lastName;
  final String login;

  String get displayName {
    final fn = firstName ?? '';
    final ln = lastName ?? '';
    final full = '$fn $ln'.trim();
    return full.isEmpty ? login : full;
  }

  factory UserPublic.fromJson(Map<String, dynamic> j) {
    return UserPublic(
      id: j['id'] as int,
      firstName: j['first_name'] as String?,
      lastName: j['last_name'] as String?,
      login: j['login'] as String,
    );
  }
}

class CommunityOverview {
  CommunityOverview({
    required this.id,
    required this.name,
    required this.description,
    required this.minTransactions,
    required this.isMember,
    required this.transactionsNeeded,
  });

  final int id;
  final String name;
  final String? description;
  final int minTransactions;
  final bool isMember;
  final int transactionsNeeded;

  factory CommunityOverview.fromJson(Map<String, dynamic> j) {
    return CommunityOverview(
      id: j['id'] as int,
      name: j['name'] as String,
      description: j['description'] as String?,
      minTransactions: j['min_transactions'] as int? ?? 0,
      isMember: j['is_member'] as bool,
      transactionsNeeded: j['transactions_needed'] as int? ?? 0,
    );
  }
}

class PostDto {
  PostDto({
    required this.id,
    required this.idSender,
    required this.idCommunity,
    required this.title,
    required this.text,
    required this.rating,
    required this.createdAt,
  });

  final int id;
  final int idSender;
  final int idCommunity;
  final String? title;
  final String? text;
  final int rating;
  final String? createdAt;

  factory PostDto.fromJson(Map<String, dynamic> j) {
    return PostDto(
      id: j['id'] as int,
      idSender: j['id_sender'] as int,
      idCommunity: j['id_community'] as int,
      title: j['title'] as String?,
      text: j['text'] as String?,
      rating: j['rating'] as int? ?? 0,
      createdAt: j['created_at'] as String?,
    );
  }
}

class CashbackDto {
  CashbackDto({
    required this.id,
    required this.amount,
    required this.place,
    required this.createdAt,
  });

  final int id;
  final double amount;
  final int place;
  final String? createdAt;

  factory CashbackDto.fromJson(Map<String, dynamic> j) {
    return CashbackDto(
      id: j['id'] as int,
      amount: (j['amount'] as num).toDouble(),
      place: j['place'] as int,
      createdAt: j['created_at'] as String?,
    );
  }
}

class RecommendItem {
  RecommendItem({
    required this.placeName,
    required this.category,
    required this.txCount,
    required this.totalAmount,
  });

  final String placeName;
  final String category;
  final int txCount;
  final double totalAmount;

  factory RecommendItem.fromJson(Map<String, dynamic> j) {
    return RecommendItem(
      placeName: j['place_name'] as String,
      category: j['category'] as String,
      txCount: (j['tx_count'] as num).toInt(),
      totalAmount: (j['total_amount'] as num).toDouble(),
    );
  }
}
