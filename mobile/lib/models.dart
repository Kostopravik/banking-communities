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
    this.categoryKey,
    this.categoryOperationsCount = 0,
    this.mccOperationsRequired = 3,
  });

  final int id;
  final String name;
  final String? description;
  final int minTransactions;
  final bool isMember;
  final int transactionsNeeded;
  final String? categoryKey;
  final int categoryOperationsCount;
  final int mccOperationsRequired;

  factory CommunityOverview.fromJson(Map<String, dynamic> j) {
    return CommunityOverview(
      id: j['id'] as int,
      name: j['name'] as String,
      description: j['description'] as String?,
      minTransactions: j['min_transactions'] as int? ?? 0,
      isMember: j['is_member'] as bool,
      transactionsNeeded: j['transactions_needed'] as int? ?? 0,
      categoryKey: j['category_key'] as String?,
      categoryOperationsCount: j['category_operations_count'] as int? ?? 0,
      mccOperationsRequired: j['mcc_operations_required'] as int? ?? 3,
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
    this.likeCount = 0,
    this.likedByMe = false,
  });

  final int id;
  final int idSender;
  final int idCommunity;
  final String? title;
  final String? text;
  final int rating;
  final String? createdAt;
  final int likeCount;
  final bool likedByMe;

  factory PostDto.fromJson(Map<String, dynamic> j) {
    return PostDto(
      id: j['id'] as int,
      idSender: j['id_sender'] as int,
      idCommunity: j['id_community'] as int,
      title: j['title'] as String?,
      text: j['text'] as String?,
      rating: j['rating'] as int? ?? 0,
      createdAt: j['created_at'] as String?,
      likeCount: j['like_count'] as int? ?? 0,
      likedByMe: j['liked_by_me'] as bool? ?? false,
    );
  }
}

class CommentDto {
  CommentDto({
    required this.id,
    required this.idSender,
    required this.senderName,
    required this.message,
    required this.createdAt,
    this.idParent,
    this.replyToName,
  });

  final int id;
  final int idSender;
  final String senderName;
  final String message;
  final String? createdAt;
  final int? idParent;
  final String? replyToName;

  factory CommentDto.fromJson(Map<String, dynamic> j) {
    return CommentDto(
      id: j['id'] as int,
      idSender: j['id_sender'] as int,
      senderName: j['sender_name'] as String,
      message: j['message'] as String,
      createdAt: j['created_at'] as String?,
      idParent: j['id_parent'] as int?,
      replyToName: j['reply_to_name'] as String?,
    );
  }
}

class BenefitDto {
  BenefitDto({
    required this.id,
    required this.title,
    required this.percent,
    required this.description,
    required this.communityId,
    required this.communityName,
    required this.isActive,
    required this.operationsNeededToJoin,
    required this.hint,
  });

  final int id;
  final String title;
  final int percent;
  final String? description;
  final int communityId;
  final String communityName;
  final bool isActive;
  final int operationsNeededToJoin;
  final String hint;

  factory BenefitDto.fromJson(Map<String, dynamic> j) {
    return BenefitDto(
      id: j['id'] as int,
      title: j['title'] as String,
      percent: (j['percent'] as num).toInt(),
      description: j['description'] as String?,
      communityId: j['community_id'] as int,
      communityName: j['community_name'] as String,
      isActive: j['is_active'] as bool,
      operationsNeededToJoin: j['operations_needed_to_join'] as int? ?? 0,
      hint: j['hint'] as String? ?? '',
    );
  }
}

class CashbackDto {
  CashbackDto({
    required this.id,
    required this.amount,
    required this.place,
    required this.createdAt,
    this.categoryKey,
    this.categoryLabel,
  });

  final int id;
  final double amount;
  final int place;
  final String? createdAt;
  final String? categoryKey;
  final String? categoryLabel;

  factory CashbackDto.fromJson(Map<String, dynamic> j) {
    return CashbackDto(
      id: j['id'] as int,
      amount: (j['amount'] as num).toDouble(),
      place: j['place'] as int,
      createdAt: j['created_at'] as String?,
      categoryKey: j['category_key'] as String?,
      categoryLabel: j['category_label'] as String?,
    );
  }
}

class CashbackOpportunityDto {
  CashbackOpportunityDto({
    required this.id,
    required this.amount,
    required this.placeMcc,
    required this.categoryKey,
    required this.categoryLabel,
    required this.operationsInCategory,
    required this.operationsRequired,
    required this.eligible,
    required this.accrued,
    required this.hint,
  });

  final int id;
  final double amount;
  final int placeMcc;
  final String? categoryKey;
  final String? categoryLabel;
  final int operationsInCategory;
  final int operationsRequired;
  final bool eligible;
  final bool accrued;
  final String hint;

  factory CashbackOpportunityDto.fromJson(Map<String, dynamic> j) {
    return CashbackOpportunityDto(
      id: j['id'] as int,
      amount: (j['amount'] as num).toDouble(),
      placeMcc: j['place_mcc'] as int,
      categoryKey: j['category_key'] as String?,
      categoryLabel: j['category_label'] as String?,
      operationsInCategory: j['operations_in_category'] as int? ?? 0,
      operationsRequired: j['operations_required'] as int? ?? 3,
      eligible: j['eligible'] as bool,
      accrued: j['accrued'] as bool,
      hint: j['hint'] as String? ?? '',
    );
  }
}

class RecommendItem {
  RecommendItem({
    required this.placeName,
    required this.category,
    required this.operationCount,
    required this.totalAmount,
  });

  final String placeName;
  final String category;
  /// Число отдельных операций в графе (рёбер) к этому месту.
  final int operationCount;
  final double totalAmount;

  factory RecommendItem.fromJson(Map<String, dynamic> j) {
    final oc = j['operation_count'] ?? j['tx_count'];
    return RecommendItem(
      placeName: j['place_name'] as String,
      category: j['category'] as String,
      operationCount: (oc as num).toInt(),
      totalAmount: (j['total_amount'] as num).toDouble(),
    );
  }
}
