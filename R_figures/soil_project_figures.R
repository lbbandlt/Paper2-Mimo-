# ============================================================
# soil_project_figures.R
# Formal figures for SOC prediction paper
# Version: select folder, auto-find CSVs
# ============================================================

library(ggplot2)
library(dplyr)
library(tidyr)
library(patchwork)

# Source palette
script_dir <- dirname(sys.frame(1)$ofile %||% ".")
if (!file.exists(file.path(script_dir, "palette.R"))) script_dir <- getwd()
source(file.path(script_dir, "palette.R"))

# ============================================================
# Select data folder (one dialog)
# ============================================================
cat("=== SOC Paper Figures ===\n")
cat("Please select the folder containing the CSV data files.\n\n")

data_dir <- choose.dir(caption = "选择包含 CSV 数据文件的文件夹")
cat("Data folder:", data_dir, "\n\n")

# Auto-load CSVs
fig1   <- read.csv(file.path(data_dir, "fig1_study_area_profiles.csv"))
fig2a  <- read.csv(file.path(data_dir, "fig2a_depth_distribution.csv"))
fig2b  <- read.csv(file.path(data_dir, "fig2b_soc_by_depth.csv"))
fig2c  <- read.csv(file.path(data_dir, "fig2c_landcover.csv"))
fig3   <- read.csv(file.path(data_dir, "fig3_formal_aggregated.csv"))
fig4   <- read.csv(file.path(data_dir, "fig4_grid_stats.csv"))
fig5   <- read.csv(file.path(data_dir, "fig5_delta_r2.csv"))

cat("All CSV loaded.\n\n")

# Select output folder
cat("Select output folder for figures...\n")
output_dir <- choose.dir(caption = "选择图件保存目录")
cat("Output folder:", output_dir, "\n\n")

# ============================================================
# Fig 2: Data Overview (3 panels)
# ============================================================
depth_order <- c("0-20cm", "20-50cm", "50-100cm", ">100cm")

p2a <- ggplot(fig2a, aes(x = factor(depth_bin, levels = depth_order), y = count)) +
  geom_col(fill = soil_brown, color = "black", linewidth = 0.3) +
  geom_text(aes(label = format(count, big.mark = ",")),
            vjust = -0.3, size = 3.5, fontface = "bold") +
  labs(x = "Depth layer", y = "Number of samples") +
  theme_classic(base_size = 13) +
  theme(plot.title = element_text(face = "bold", size = 14))

p2b <- ggplot(fig2b, aes(x = factor(depth_bin, levels = depth_order), y = log_SOC)) +
  geom_boxplot(fill = soil_brown, alpha = 0.7, outlier.size = 0.3) +
  labs(x = "Depth layer", y = "log(1 + SOC) [g/kg]") +
  theme_classic(base_size = 13)

lc_colors <- c("Cropland" = warn_orange, "Forest" = forest_green,
               "Grassland" = water_blue, "Other" = "#BAB0AC")
p2c <- ggplot(fig2c, aes(x = "", y = count, fill = CLCD)) +
  geom_col(width = 1) +
  coord_polar("y") +
  scale_fill_manual(values = lc_colors) +
  geom_text(aes(label = sprintf("%1.1f%%", count / sum(count) * 100)),
            position = position_stack(vjust = 0.5), size = 4, fontface = "bold") +
  labs(fill = "Land cover") +
  theme_void(base_size = 13)

fig2_plot <- p2a + p2b + p2c +
  plot_layout(widths = c(1, 1, 0.8)) +
  plot_annotation(tag_levels = "A")

ggsave(file.path(output_dir, "fig2_data_overview.png"), fig2_plot,
       width = 15, height = 5, dpi = 300)
ggsave(file.path(output_dir, "fig2_data_overview.pdf"), fig2_plot,
       width = 15, height = 5)
cat("fig2 saved.\n")

# ============================================================
# Fig 3: Model Performance (2 panels)
# ============================================================
cv_labels <- c("Random_5fold" = "Random CV", "Spatial_block" = "Spatial Block CV")
cv_colors <- c("Random_5fold" = cv_blue, "Spatial_block" = cv_red)

fig3a_df <- fig3 %>%
  select(cv_type, model, R2_all_mean, R2_all_std) %>%
  mutate(cv_label = recode(cv_type, !!!cv_labels))

p3a <- ggplot(fig3a_df, aes(x = model, y = R2_all_mean, fill = cv_label)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.6,
           color = "black", linewidth = 0.3) +
  geom_errorbar(aes(ymin = R2_all_mean - R2_all_std, ymax = R2_all_mean + R2_all_std),
                position = position_dodge(width = 0.7), width = 0.15) +
  geom_text(aes(label = sprintf("%.3f", R2_all_mean), group = cv_label),
            position = position_dodge(width = 0.7), vjust = -0.5, size = 3.2, fontface = "bold") +
  scale_fill_manual(values = cv_colors) +
  labs(x = "Model", y = expression(R^2), fill = "Validation") +
  theme_classic(base_size = 13) +
  theme(legend.position = c(0.02, 0.98), legend.justification = c(0, 1)) +
  ylim(0, 0.82)

depth_labels <- c("0-20cm", "20-50cm", "50-100cm", ">100cm")
depth_df <- fig3 %>%
  filter(cv_type == "Spatial_block") %>%
  select(model, starts_with("R2_") & !starts_with("R2_all") &
           !starts_with("R2_surface") & !starts_with("R2_deep")) %>%
  pivot_longer(cols = -model, names_to = "metric", values_to = "value") %>%
  mutate(
    depth_bin = case_when(
      grepl("0.20", metric) ~ "0-20cm",
      grepl("20.50", metric) ~ "20-50cm",
      grepl("50.100", metric) ~ "50-100cm",
      grepl("X.100", metric) ~ ">100cm",
      TRUE ~ NA_character_
    ),
    stat = ifelse(grepl("_std", metric), "std", "mean")
  ) %>%
  filter(!is.na(depth_bin)) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  mutate(depth_bin = factor(depth_bin, levels = depth_labels))

p3b <- ggplot(depth_df, aes(x = depth_bin, y = mean, color = model, group = model)) +
  geom_line(linewidth = 1.2) +
  geom_point(size = 3) +
  geom_errorbar(aes(ymin = mean - std, ymax = mean + std), width = 0.2) +
  scale_color_manual(values = model_palette) +
  labs(x = "Depth layer", y = expression(R^2 ~ "(Spatial Block CV)"), color = "Model") +
  theme_classic(base_size = 13) +
  theme(legend.position = c(0.98, 0.98), legend.justification = c(1, 1)) +
  ylim(-0.05, 0.7)

fig3_plot <- p3a + p3b + plot_annotation(tag_levels = "A")
ggsave(file.path(output_dir, "fig3_performance.png"), fig3_plot,
       width = 13, height = 5.5, dpi = 300)
ggsave(file.path(output_dir, "fig3_performance.pdf"), fig3_plot,
       width = 13, height = 5.5)
cat("fig3 saved.\n")

# ============================================================
# Fig 4: Spatial Grid Map
# ============================================================
p4a <- ggplot(fig4, aes(x = lon_mean, y = lat_mean)) +
  geom_point(aes(size = n_profiles, color = n_samples), alpha = 0.85) +
  scale_color_gradient(low = "#FFF8DC", high = "#D2691E") +
  scale_size_continuous(range = c(2, 10)) +
  labs(x = "Longitude (°)", y = "Latitude (°)",
       color = "Samples", size = "Profiles") +
  theme_classic(base_size = 13) +
  coord_fixed(ratio = 1.5)

p4b <- ggplot(fig4, aes(x = lon_mean, y = lat_mean)) +
  geom_point(aes(size = n_profiles, color = SOC_mean), alpha = 0.85) +
  scale_color_gradient(low = "#F0FFF0", high = "#228B22") +
  scale_size_continuous(range = c(2, 10)) +
  labs(x = "Longitude (°)", y = "Latitude (°)",
       color = "Mean SOC\n(g/kg)", size = "Profiles") +
  theme_classic(base_size = 13) +
  coord_fixed(ratio = 1.5)

fig4_plot <- p4a + p4b + plot_annotation(tag_levels = "A")
ggsave(file.path(output_dir, "fig4_spatial_grid.png"), fig4_plot,
       width = 14, height = 5.5, dpi = 300)
ggsave(file.path(output_dir, "fig4_spatial_grid.pdf"), fig4_plot,
       width = 14, height = 5.5)
cat("fig4 saved.\n")

# ============================================================
# Fig 5: ΔR²
# ============================================================
depth_group_labels <- c("all" = "All depths", "surface" = "Surface (0-30 cm)",
                        "deep" = "Deep (>30 cm)")
fig5$depth_label <- recode(fig5$depth_group, !!!depth_group_labels)

p5 <- ggplot(fig5, aes(x = depth_label, y = delta_R2, fill = model)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.6,
           color = "black", linewidth = 0.3) +
  geom_text(aes(label = sprintf("+%.3f", delta_R2), group = model),
            position = position_dodge(width = 0.7), vjust = -0.3, size = 3, fontface = "bold") +
  scale_fill_manual(values = model_palette) +
  geom_hline(yintercept = 0, linewidth = 0.8) +
  labs(x = "Depth group", y = expression(Delta * R^2 ~ "(Random - Spatial)"), fill = "Model") +
  theme_classic(base_size = 13) +
  theme(legend.position = c(0.02, 0.98), legend.justification = c(0, 1))

ggsave(file.path(output_dir, "fig5_delta_r2.png"), p5,
       width = 10, height = 5.5, dpi = 300)
ggsave(file.path(output_dir, "fig5_delta_r2.pdf"), p5,
       width = 10, height = 5.5)
cat("fig5 saved.\n")

# ============================================================
# Done
# ============================================================
cat("\n=== All figures saved to:", output_dir, "===\n")
