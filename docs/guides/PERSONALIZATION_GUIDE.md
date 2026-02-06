# Daily Feed - Personalization Guide

This guide explains how to use the personalization features in Daily Feed.

---

## 🚀 Quick Start

### 1. Complete Onboarding

```bash
curl -X POST http://localhost:8000/api/v1/users/onboarding \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "interests": ["AI", "Technology", "Business"],
    "preferred_sources": ["TechCrunch", "The Verge", "Hacker News"],
    "summary_length": "medium",
    "delivery_time": "08:00",
    "daily_limit": 10
  }'
```

### 2. Generate Your First Personalized Digest

```bash
curl -X POST http://localhost:8000/api/v1/users/me/digest/generate
```

Response:
```json
{
  "id": "uuid-here",
  "created_at": "2026-02-04T20:30:00",
  "articles": [
    {
      "id": 1,
      "title": "AI Breakthrough",
      "source": "TechCrunch",
      "category": "AI",
      "score": 0.85,
      "score_breakdown": {
        "topic": 0.9,
        "source": 1.0,
        "freshness": 0.92,
        "quality": 0.75,
        "diversity": 0.5
      }
    }
  ],
  "personalization_score": 0.82,
  "status": "pending"
}
```

### 3. Provide Feedback

Like an article:
```bash
curl -X POST http://localhost:8000/api/v1/users/me/feedback \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1, "feedback": "like"}'
```

Dislike an article:
```bash
curl -X POST http://localhost:8000/api/v1/users/me/feedback \
  -H "Content-Type: application/json" \
  -d '{"article_id": 2, "feedback": "dislike"}'
```

Save for later:
```bash
curl -X POST http://localhost:8000/api/v1/users/me/feedback \
  -H "Content-Type: application/json" \
  -d '{"article_id": 3, "feedback": "save"}'
```

---

## 📊 Understanding Your Scores

### Personalization Score Breakdown

Each article receives a score (0-1) based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Topic Interest** | 35% | How much you like this topic |
| **Source Preference** | 20% | Your trust in this publisher |
| **Freshness** | 25% | How recent (adjustable) |
| **Quality** | 15% | Content quality assessment |
| **Diversity** | 5% | Avoiding filter bubbles |

### Freshness Modes

```bash
# Breaking news mode - prioritize recency
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{"freshness_preference": "breaking"}'

# Daily mode - balanced (default)
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{"freshness_preference": "daily"}'

# Weekly mode - prioritize quality over speed
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{"freshness_preference": "weekly"}'
```

---

## 🎛️ Customizing Preferences

### Update Topic Interests

```bash
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "topic_interests": {
      "AI": 0.95,
      "Technology": 0.8,
      "Business": 0.6,
      "Science": 0.4
    }
  }'
```

### Block Topics/Sources

```bash
# Never show Crypto or Politics
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "exclude_topics": ["Crypto", "Politics"],
    "exclude_sources": ["UnreliableNews"]
  }'
```

### Adjust Summary Length

```bash
# Short summaries (1-2 paragraphs)
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{"summary_length": "short"}'

# Medium summaries (default)
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{"summary_length": "medium"}'

# Long summaries (full analysis)
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{"summary_length": "long"}'
```

---

## 📈 Viewing Your Stats

```bash
curl http://localhost:8000/api/v1/users/me/stats
```

Response:
```json
{
  "total_articles_read": 47,
  "total_articles_saved": 12,
  "average_reading_time": 145,
  "favorite_topics": [
    {"topic": "AI", "count": 23},
    {"topic": "Technology", "count": 15}
  ],
  "favorite_sources": [
    {"source": "TechCrunch", "count": 18},
    {"source": "The Verge", "count": 12}
  ],
  "digest_open_rate": 78.5,
  "last_7_days_activity": [5, 3, 7, 4, 6, 8, 5]
}
```

---

## 🧠 How Learning Works

### Automatic Adaptation

The system learns from your behavior:

| Your Action | Effect on Model |
|-------------|-----------------|
| Read > 60s | +5% topic interest |
| Click "Like" | +5% topic, +3% source |
| Save article | +10% topic interest |
| Click "Dislike" | -8% topic interest |
| Dismiss quickly | -3% topic interest |

### Interest Decay

Over time, interests decay toward neutral (0.5) if not reinforced:
- Prevents stale preferences
- Allows natural evolution of interests
- Weekly decay: 5%

### Diversity Protection

The system ensures you don't get trapped in a filter bubble:
- 5% diversity boost for underrepresented topics
- Minimum topic variety in each digest
- Occasional "discovery" articles from new topics

---

## 🔧 Advanced Configuration

### Delivery Schedule

```bash
# Set delivery time and timezone
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "delivery_time": "07:30",
    "timezone": "America/New_York"
  }'
```

### Daily Article Limit

```bash
# Reduce to 5 articles per digest
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{"daily_article_limit": 5}'
```

### Diversity Boost

```bash
# Increase diversity (0.0 - 1.0)
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{"diversity_boost": 0.2}'
```

### Disable Auto-Adjustment

```bash
# Stop automatic learning
curl -X PATCH http://localhost:8000/api/v1/users/me/preferences \
  -H "Content-Type: application/json" \
  -d '{"auto_adjust_interests": false}'
```

---

## 📱 Frontend Integration

### React Example: Like Button

```jsx
function LikeButton({ articleId }) {
  const [liked, setLiked] = useState(false);
  
  const handleLike = async () => {
    await fetch('/api/v1/users/me/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        article_id: articleId,
        feedback: liked ? 'dismiss' : 'like'
      })
    });
    setLiked(!liked);
  };
  
  return (
    <button onClick={handleLike}>
      {liked ? '❤️' : '🤍'}
    </button>
  );
}
```

### React Example: Personalized Feed

```jsx
function PersonalizedFeed() {
  const [digest, setDigest] = useState(null);
  
  useEffect(() => {
    fetch('/api/v1/users/me/digest/generate', { method: 'POST' })
      .then(r => r.json())
      .then(setDigest);
  }, []);
  
  return (
    <div>
      <h2>Your Personalized Digest</h2>
      <p>Match Score: {digest?.personalization_score}%</p>
      {digest?.articles.map(article => (
        <ArticleCard 
          key={article.id} 
          article={article}
          scoreBreakdown={article.score_breakdown}
        />
      ))}
    </div>
  );
}
```

---

## 🎯 Best Practices

1. **Complete Onboarding** - The more initial info, the better first digests
2. **Provide Feedback** - Like/dislike helps the system learn faster
3. **Save Articles** - Strong signal of what you value
4. **Review Stats** - Check `/users/me/stats` to see your reading patterns
5. **Adjust Diversity** - Increase if you feel stuck in a bubble
6. **Use Freshness Modes** - Breaking for news, Weekly for analysis

---

## 🔍 Troubleshooting

### Digests feel repetitive?
- Increase `diversity_boost`
- Check `exclude_topics` isn't too broad
- Use "dislike" on repetitive content

### Missing important topics?
- Add topics to `topic_interests` with high weight
- Check if topic is in `exclude_topics`
- Switch to "breaking" freshness mode

### Too many articles?
- Reduce `daily_article_limit`
- Increase `exclude_sources` list
- Lower topic interest weights

### Not learning?
- Check `auto_adjust_interests` is enabled
- Provide explicit feedback (like/dislike)
- Ensure interactions are being recorded
