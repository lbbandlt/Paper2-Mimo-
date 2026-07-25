# Fig 8: Covariate Shift with Depth
# R script — reads data from fig8_covariate_shift_data.csv

library(ggplot2)
library(patchwork)

# ============================================================
# Data (auto-load from CSV)
# ============================================================
data_dir <- choose.dir(caption = "Select folder containing fig8_covariate_shift_data.csv")
fig8_data <- read.csv(file.path(data_dir, "fig8_covariate_shift_data.csv"))

surface_covs <- subset(fig8_data, depth_layer == "Surface (0-20 cm)")
surface_covs$x_pos <- seq_len(nrow(surface_covs))

deep_all <- subset(fig8_data, depth_layer == "Deep (>100 cm)")
deep_all$x_pos <- seq_len(nrow(deep_all))
deep_surface <- subset(deep_all, covariate_type == "surface")
deep_new <- subset(deep_all, covariate_type == "deep_specific")
deep_new$x_pos <- c(1.5, 2.5)

# ============================================================
# Panel A: Surface
# ============================================================
p1 <- ggplot() +
  annotate("rect", xmin = -Inf, xmax = Inf, ymin = -Inf, ymax = Inf,
           fill = "#8BC34A", alpha = 0.15) +
  geom_col(data = surface_covs,
           aes(x = x_pos, y = contribution, fill = covariate),
           width = 0.6, alpha = 0.7, color = "black", linewidth = 0.5) +
  geom_text(data = surface_covs,
            aes(x = x_pos, y = contribution + 0.03, label = covariate),
            fontface = "bold", size = 4) +
  geom_text(data = surface_covs,
            aes(x = x_pos, y = contribution / 2,
                label = sprintf("%.0f%%", contribution * 100)),
            fontface = "bold", size = 3.5, color = "white") +
  annotate("label", x = 2, y = 0.3, label = "SOC\nR^2 = 0.57",
           size = 6, fontface = "bold", color = "#1B5E20",
           fill = "white", label.size = 1.5) +
  annotate("label", x = 2, y = 0.05,
           label = "Strong coupling: vegetation & climate\ncontrol topsoil carbon",
           size = 3.5, fontface = "bold", color = "#2E7D32",
           fill = "#E8F5E9", label.size = 0.8) +
  scale_fill_manual(values = c("NDVI" = "#4CAF50", "MAT / PET" = "#FF9800",
                                "Land cover" = "#8D6E63")) +
  labs(title = "A) Surface soil (0-20 cm)", y = "Covariate contribution", x = NULL) +
  coord_cartesian(ylim = c(0, 1)) +
  theme_classic(base_size = 13) +
  theme(legend.position = "none",
        axis.text.x = element_blank(), axis.ticks.x = element_blank(),
        plot.title = element_text(face = "bold", size = 14))

# ============================================================
# Panel B: Deep
# ============================================================
p2 <- ggplot() +
  annotate("rect", xmin = -Inf, xmax = Inf, ymin = -Inf, ymax = Inf,
           fill = "#FF9800", alpha = 0.15) +
  geom_col(data = deep_surface,
           aes(x = x_pos, y = contribution, fill = covariate),
           width = 0.6, alpha = 0.2, color = "black", linewidth = 0.3,
           linetype = "dashed") +
  geom_text(data = deep_surface,
            aes(x = x_pos, y = contribution + 0.03, label = covariate),
            fontface = "bold", size = 4, alpha = 0.35) +
  geom_col(data = deep_new,
           aes(x = x_pos, y = contribution),
           width = 0.6, alpha = 0.3, fill = "#795548", color = "black", linewidth = 0.5) +
  geom_text(data = deep_new,
            aes(x = x_pos, y = contribution + 0.03, label = covariate),
            fontface = "bold", size = 3.5) +
  geom_text(data = deep_new,
            aes(x = x_pos, y = contribution / 2, label = "X"),
            size = 8, fontface = "bold", color = "#D32F2F") +
  annotate("label", x = 2, y = 0.3, label = "SOC\nR^2 = 0.29",
           size = 6, fontface = "bold", color = "#BF360C",
           fill = "white", label.size = 1.5) +
  annotate("label", x = 2, y = 0.05,
           label = "Weak coupling: surface covariates\nblind to deep soil processes",
           size = 3.5, fontface = "bold", color = "#BF360C",
           fill = "#FFF3E0", label.size = 0.8) +
  scale_fill_manual(values = c("NDVI" = "#4CAF50", "MAT / PET" = "#FF9800",
                                "Land cover" = "#8D6E63")) +
  labs(title = "B) Deep soil (>100 cm)", y = "Covariate contribution", x = NULL) +
  coord_cartesian(ylim = c(0, 1)) +
  theme_classic(base_size = 13) +
  theme(legend.position = "none",
        axis.text.x = element_blank(), axis.ticks.x = element_blank(),
        plot.title = element_text(face = "bold", size = 14))

# ============================================================
# Combine and save
# ============================================================
output_dir <- choose.dir(caption = "Select output folder")
fig8 <- p1 + p2 + plot_annotation(tag_levels = "A")

ggsave(file.path(output_dir, "fig8_covariate_shift.png"), fig8,
       width = 14, height = 7, dpi = 300)
ggsave(file.path(output_dir, "fig8_covariate_shift.pdf"), fig8,
       width = 14, height = 7)
cat("Saved: fig8_covariate_shift.png/pdf\n")
