def predict_overflow(fill_level, hours_since_last_collection):
    DAYS_20_IN_HOURS =  20 * 24

    if fill_level >= 80 and hours_since_last_collection >= DAYS_20_IN_HOURS:
        return True
    return False
