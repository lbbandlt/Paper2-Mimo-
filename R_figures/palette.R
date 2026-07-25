# ============================================================
# palette.R — Color palette for SOC prediction paper
# ============================================================
# Semantic colors (low-saturation, publication-friendly)

# Soil / earth tones
soil_brown    <- "#D2B48C"
soil_yellow   <- "#F0E68C"
soil_light    <- "#EDE0C8"

# Water / moisture
water_blue    <- "#A6C8E0"

# Forest / vegetation
forest_green  <- "#90C695"

# Time / migration
time_purple   <- "#B8A9C9"

# Warning / degradation
warn_orange   <- "#E8917A"
warn_red      <- "#E15759"

# CV comparison
cv_blue       <- "#4E79A7"
cv_red        <- "#E15759"

# Model palette (for multi-model figures)
model_palette <- c(
  "LinearReg" = "#4E79A7",
  "Ridge"     = "#76B7B2",
  "RF"        = "#F28E2B",
  "XGBoost"   = "#59A14F"
)

# Climate zone palette
climate_palette <- c(
  "Alpine"    = "#B8A9C9",
  "Temperate" = "#90C695",
  "Warm"      = "#F28E2B",
  "Tropical"  = "#E15759"
)

# Land cover palette
lc_palette <- c(
  "Cropland"  = "#F28E2B",
  "Forest"    = "#59A14F",
  "Grassland" = "#76B7B2",
  "Other"     = "#BAB0AC"
)
