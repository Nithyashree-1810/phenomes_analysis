

# ---------------------------------------
# Phoneme Performance
# ---------------------------------------
class PhonemePerformance(Base):
    __tablename__ = "phoneme_performance"
    __table_args__ = (
        UniqueConstraint("user_id", "phoneme", name="uq_user_phoneme"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # FK → references the INTEGER column user_pronunciation_profile.user_id
    user_id = Column(
        Integer,
        ForeignKey("user_pronunciation_profile.user_id", ondelete="CASCADE"),
        nullable=False
    )

    phoneme = Column(String(50), nullable=False)
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    accuracy_pct = Column(Numeric(5, 2), default=0)
    last_attempted_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    profile = relationship(
        "UserPronunciationProfile",
        back_populates="phoneme_stats",
        primaryjoin="PhonemePerformance.user_id==UserPronunciationProfile.user_id"
    )