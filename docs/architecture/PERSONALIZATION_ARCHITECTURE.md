# Personalization Architecture - Daily Feed

**Vision:** Transform from a generic news aggregator into an intelligent, learning content companion that knows what each user cares about.

---

## 🎯 Core Concepts

### 1. User-Centric Design
```
OLD: System fetches → Summarizes → Delivers (same to everyone)
NEW: User prefs → Personalized fetch → Ranked → Adaptive delivery
```

### 2. Learning Loop
```
Content → User Action → Feedback → Model Update → Better Recommendations
```

### 3. Key Personalization Dimensions
| Dimension | Description | Example |
|-----------|-------------|---------|
| **Topics** | Subject interests | AI, Climate, Startups |
| **Sources** | Preferred publishers | TechCrunch > Verge |
| **Depth** | Summary detail level | Short (1-min) vs Deep (5-min) |
| **Timing** | When to deliver | Morning 8am, Evening 6pm |
| **Freshness** | How recent content | Breaking news vs Weekly digest |

---

## 🏗️ Architecture Components

### Database Models

```python
# User Profile
class User:
    id: UUID
    email: str
    name: str
    created_at: datetime
    onboarding_completed: bool

# User Preferences  
class UserPreferences:
    user_id: UUID
    
    # Topics (weighted interests)
    topic_interests: Dict[str, float]  # {"AI": 0.9, "Crypto": 0.3}
    
    # Sources (priority ranking)
    source_preferences: Dict[str, float]  # {"TechCrunch": 1.0, "Verge": 0.7}
    
    # Content preferences
    summary_length: str  # "short", "medium", "long"
    daily_article_limit: int  # Max articles per digest
    delivery_time: time  # When to send digest
    timezone: str
    
    # Filters
    exclude_topics: List[str]  # Never show these
    exclude_sources: List[str]  # Block these sources
    
    # Advanced
    language_preference: str  # "en", "auto"
    include_reading_time: bool

# User Interactions (Learning Data)
class UserInteraction:
    id: UUID
    user_id: UUID
    article_id: UUID
    
    # Engagement tracking
    delivered_at: datetime
    opened_at: datetime  
    read_duration_seconds: int
    
    # Explicit feedback
    rating: int  # 1-5 stars or -1, 0, 1 (dislike/neutral/like)
    saved: bool
    shared: bool
    
    # Implicit signals
    scrolled_depth: float  # % of content viewed
    clicked_links: int
    
    # Derived score
    engagement_score: float  # Calculated composite score

# Personalized Digest
class PersonalizedDigest:
    id: UUID
    user_id: UUID
    created_at: datetime
    
    # Content selection
    articles: List[DigestArticle]  # Ranked & personalized
    
    # Personalization metadata
    personalization_score: float  # How well it matches user
    diversity_score: float  # Topic diversity
    freshness_score: float  # Recency weighting
    
    # Performance
    opened: bool
    click_through_rate: float
```

### ML/Ranking Pipeline

```python
class PersonalizationEngine:
    """Core recommendation engine"""
    
    def rank_articles(
        self, 
        articles: List[Article], 
        user: User
    ) -> List[ScoredArticle]:
        """Score and rank articles for a specific user"""
        
        scores = []
        for article in articles:
            score = self._calculate_score(article, user)
            scores.append(ScoredArticle(article, score))
        
        # Sort by score descending
        return sorted(scores, key=lambda x: x.score, reverse=True)
    
    def _calculate_score(self, article, user) -> float:
        """Multi-factor scoring algorithm"""
        
        # Topic match (0-1)
        topic_score = self._topic_similarity(
            article.category, 
            user.preferences.topic_interests
        )
        
        # Source preference (0-1)
        source_score = user.preferences.source_preferences.get(
            article.source_name, 0.5
        )
        
        # Recency boost (exponential decay)
        age_hours = (now() - article.published_at).hours
        freshness_score = exp(-age_hours / 24)  # 24h half-life
        
        # Quality score (from critique tool)
        quality_score = article.quality_score / 10.0
        
        # Personalized recency (based on user's reading patterns)
        if user.preferences.freshness_preference == "breaking":
            freshness_weight = 0.4
        elif user.preferences.freshness_preference == "weekly":
            freshness_weight = 0.1
        else:  # daily
            freshness_weight = 0.25
        
        # Weighted combination
        final_score = (
            topic_score * 0.35 +
            source_score * 0.20 +
            freshness_score * freshness_weight +
            quality_score * 0.15 +
            # Boost underrepresented topics (diversity)
            diversity_boost(article.category) * 0.05
        )
        
        return final_score
```

### Adaptive Learning

```python
class UserModelTrainer:
    """Updates user preferences based on interactions"""
    
    def update_from_interaction(self, interaction: UserInteraction):
        """Learn from user actions"""
        
        article = interaction.article
        user = interaction.user
        
        # Positive signals increase topic weights
        if interaction.rating > 0 or interaction.read_duration > 60:
            self._reinforce_topic(
                user, 
                article.category, 
                delta=0.05 * interaction.rating
            )
            self._reinforce_source(
                user,
                article.source_name,
                delta=0.03
            )
        
        # Negative signals decrease weights
        if interaction.rating < 0 or interaction.read_duration < 5:
            self._reduce_topic(
                user,
                article.category,
                delta=0.08  # Penalize more than reward (avoid filter bubble)
            )
        
        # "More like this" explicit feedback
        if interaction.user_requested_similar:
            for topic in article.topics:
                self._reinforce_topic(user, topic, delta=0.1)
```

---

## 🔄 Personalization Workflow

### 1. User Onboarding
```
Signup → Interest Selection → Source Preferences → Delivery Setup → Ready
```

### 2. Daily Flow
```
Fetch Articles (all sources)
    ↓
Filter by User Preferences (exclude blocked topics/sources)
    ↓
Score Each Article (personalization engine)
    ↓
Select Top N (respecting diversity)
    ↓
Generate Personalized Digest
    ↓
Deliver at User's Preferred Time
    ↓
Track Interactions → Update User Model
```

### 3. Feedback Loop
```
User opens article → Track read time → Implicit +signal
User rates article → Explicit +/-signal  
User saves article → Strong +signal
User dismisses → Weak -signal
```

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] User model & authentication
- [ ] Preferences schema & storage
- [ ] Basic API endpoints for user management

### Phase 2: Personalization Engine (Week 2)
- [ ] Article scoring algorithm
- [ ] Topic extraction from articles
- [ ] User interest inference

### Phase 3: Learning Loop (Week 3)
- [ ] Interaction tracking
- [ ] Preference updates from feedback
- [ ] A/B testing framework

### Phase 4: User Experience (Week 4)
- [ ] Onboarding flow
- [ ] User dashboard
- [ ] Feedback UI (thumbs, save, share)

---

## 📊 Success Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Open Rate | >40% | Are users engaging? |
| Read Completion | >60% | Is content relevant? |
| Explicit Feedback | 10%/week | Learning signal volume |
| Retention (7-day) | >50% | Long-term value |
| Diversity Score | >0.3 | Avoid filter bubble |

---

## 🎨 User Experience Principles

1. **Progressive Disclosure**: Start simple, reveal advanced features over time
2. **Transparency**: Show why content was recommended
3. **Control**: Easy to correct/course-correct recommendations
4. **Privacy First**: Local-first where possible, clear data usage
