# Figures 2–5 for the revised SOC spatial-generalization manuscript
# Run this script from its own directory. Outputs are written to figures_rebuilt/.

required <- c("ggplot2", "dplyr", "tidyr", "readr", "patchwork", "scales", "ragg", "svglite")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing) > 0) {
  install.packages(missing, repos = "https://cloud.r-project.org")
}
suppressPackageStartupMessages({
  library(ggplot2); library(dplyr); library(tidyr); library(readr)
  library(patchwork); library(scales); library(ragg)
})

script_path <- tryCatch(normalizePath(sys.frame(1)$ofile), error = function(e) NA_character_)
script_dir <- if (length(script_path) == 1 && !is.na(script_path)) dirname(script_path) else getwd()
if (!dir.exists(file.path(script_dir, "source_data_rebuilt"))) script_dir <- getwd()
data_dir <- file.path(script_dir, "source_data_rebuilt")
out_dir <- file.path(script_dir, "figures_rebuilt")
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

depth_levels <- c("0-20cm", "20-50cm", "50-100cm", "100-200cm")
depth_labels <- c("0–20 cm", "20–50 cm", "50–100 cm", "100–200 cm")
depth_cols <- c("0-20cm"="#356B8C", "20-50cm"="#78ABC5", "50-100cm"="#9486B8", "100-200cm"="#D9A15F")
model_cols <- c("RF"="#356B8C", "Ridge"="#8B8B8B")
red <- "#B95C59"; grey <- "#777777"; lightblue <- "#BFD7E5"

theme_paper <- function(base_size = 9) {
  theme_classic(base_size = base_size, base_family = "Times New Roman") +
    theme(
      axis.line = element_line(linewidth = 0.45, colour = "black"),
      axis.ticks = element_line(linewidth = 0.45, colour = "black"),
      axis.title = element_text(size = base_size + 1, colour = "black"),
      axis.text = element_text(size = base_size, colour = "black"),
      legend.title = element_blank(), legend.text = element_text(size = base_size),
      strip.background = element_blank(), strip.text = element_text(face = "bold", size = base_size + 0.5),
      plot.tag = element_text(face = "bold", size = base_size + 4),
      plot.margin = margin(6, 8, 6, 6), panel.grid = element_blank()
    )
}
theme_set(theme_paper())

save_figure <- function(p, name, width_mm = 183, height_mm = 120) {
  w <- width_mm / 25.4; h <- height_mm / 25.4
  ggsave(file.path(out_dir, paste0(name, ".png")), p, width = w, height = h,
         units = "in", dpi = 600, device = ragg::agg_png, bg = "white")
  ggsave(file.path(out_dir, paste0(name, ".tiff")), p, width = w, height = h,
         units = "in", dpi = 600, device = ragg::agg_tiff, compression = "lzw", bg = "white")
  ggsave(file.path(out_dir, paste0(name, ".svg")), p, width = w, height = h,
         units = "in", device = svglite::svglite, bg = "white")
  ggsave(file.path(out_dir, paste0(name, ".pdf")), p, width = w, height = h,
         units = "in", device = cairo_pdf, family = "Times New Roman", bg = "white")
}

# ---------------- Figure 2: depth harmonization and retained data ----------------
cov <- read_csv(file.path(data_dir, "coverage_threshold_summary.csv"), show_col_types = FALSE) %>%
  mutate(standard_depth = factor(standard_depth, depth_levels),
         threshold = factor(coverage_threshold, c(0.5, 0.8, 1.0), c("≥50%", "≥80%", "100%")))

p2a <- cov %>% filter(coverage_threshold == 0.5) %>%
  ggplot(aes(standard_depth, n_profiles, fill = standard_depth)) +
  geom_col(width = 0.68, colour = "black", linewidth = 0.35) +
  geom_text(aes(label = comma(n_profiles)), vjust = -0.45, size = 3, family = "Times New Roman") +
  scale_fill_manual(values = depth_cols, guide = "none") +
  scale_x_discrete(labels = depth_labels) +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.12))) +
  labs(x = NULL, y = "Retained profiles (n)")

p2b <- ggplot(cov, aes(standard_depth, n_profiles, colour = threshold, group = threshold)) +
  geom_line(linewidth = 0.75) + geom_point(size = 2.4, shape = 21, fill = "white", stroke = 0.8) +
  scale_colour_manual(values = c("≥50%"="#356B8C", "≥80%"="#7CA8BF", "100%"="#B5B5B5")) +
  scale_x_discrete(labels = depth_labels) + scale_y_continuous(labels = comma) +
  labs(x = NULL, y = "Profiles retained (n)") +
  theme(legend.position = "bottom")

p2c <- cov %>% filter(coverage_threshold == 0.5) %>%
  ggplot(aes(standard_depth, SOC_median_g_kg, fill = standard_depth)) +
  geom_col(width = 0.68, colour = "black", linewidth = 0.35) +
  geom_text(aes(label = sprintf("%.2f", SOC_median_g_kg)), vjust = -0.45,
            size = 3, family = "Times New Roman") +
  scale_fill_manual(values = depth_cols, guide = "none") + scale_x_discrete(labels = depth_labels) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.13))) +
  labs(x = NULL, y = expression("Median SOC (g "*kg^{-1}*")"))

fig2 <- (p2a | p2b | p2c) + plot_annotation(tag_levels = "A")
save_figure(fig2, "Figure2_depth_harmonization", 183, 76)

# ---------------- Figure 3: validation design and spatial distance ----------------
multi <- read_csv(file.path(data_dir, "multiscale_scale_summary.csv"), show_col_types = FALSE)
random <- read_csv(file.path(data_dir, "corrected_summary.csv"), show_col_types = FALSE) %>%
  filter(model %in% c("RF", "Ridge"), subset == "all", grepl("Random_profile", cv_design)) %>%
  group_by(model) %>% summarise(R2 = mean(R2_log_mean), R2_sd = sd(R2_log_mean), .groups = "drop")

p3a_dat <- multi %>% filter(subset == "all", model %in% c("RF", "Ridge"))
p3a <- ggplot(p3a_dat, aes(grid_scale_deg, R2_mean, colour = model, shape = model)) +
  geom_hline(data = random, aes(yintercept = R2, colour = model), linetype = 2, linewidth = 0.55, show.legend = FALSE) +
  geom_errorbar(aes(ymin = R2_mean-R2_sd_offsets, ymax = R2_mean+R2_sd_offsets), width = 0.16, linewidth = 0.5) +
  geom_line(linewidth = 0.85) + geom_point(size = 2.7, fill = "white", stroke = 0.9) +
  scale_colour_manual(values = model_cols) + scale_shape_manual(values = c(RF=21, Ridge=24)) +
  scale_x_continuous(breaks = c(2.5,5,7.5,10)) +
  labs(x = "Spatial block size (°)", y = expression(R[log]^2)) + theme(legend.position = "bottom")

p3b <- p3a_dat %>% filter(model == "RF") %>%
  ggplot(aes(distance_median_mean_km, R2_mean)) +
  geom_errorbar(aes(ymin=R2_mean-R2_sd_offsets, ymax=R2_mean+R2_sd_offsets), width=4, colour="#356B8C") +
  geom_smooth(method = "lm", se = TRUE, colour = "#356B8C", fill = lightblue, linewidth = 0.7) +
  geom_point(size = 2.7, shape = 21, fill = "white", colour = "#356B8C", stroke = 0.9) +
  labs(x = "Median test–train distance (km)", y = expression(R[log]^2))

p3c_dat <- multi %>% filter(model == "RF", subset %in% depth_levels) %>%
  mutate(subset = factor(subset, depth_levels))
p3c <- ggplot(p3c_dat, aes(grid_scale_deg, R2_mean, colour = subset, shape = subset)) +
  geom_errorbar(aes(ymin=R2_mean-R2_sd_offsets, ymax=R2_mean+R2_sd_offsets), width=.15, linewidth=.4) +
  geom_line(linewidth=.75) + geom_point(size=2.3, fill="white", stroke=.8) +
  scale_colour_manual(values=depth_cols, labels=depth_labels) + scale_shape_manual(values=c(21,22,23,24), labels=depth_labels) +
  scale_x_continuous(breaks=c(2.5,5,7.5,10)) + labs(x="Spatial block size (°)", y=expression(R[log]^2)) +
  theme(legend.position="bottom")

fig3 <- (p3a | p3b | p3c) + plot_annotation(tag_levels = "A")
save_figure(fig3, "Figure3_multiscale_validation", 183, 78)

# ---------------- Figure 4: explicit buffers and depth dependence ----------------
buff <- read_csv(file.path(data_dir, "buffered_summary.csv"), show_col_types = FALSE)
ctrl <- read_csv(file.path(data_dir, "buffer_vs_size_matched_summary.csv"), show_col_types = FALSE)

p4a_d1 <- buff %>% filter(model=="RF", subset=="all") %>% transmute(buffer=buffer_km, method="Buffered", R2=R2_mean)
p4a_d2 <- ctrl %>% filter(subset=="all") %>% transmute(buffer=buffer_km_target, method="Equal-size control", R2=R2_size_matched_mean)
p4a_dat <- bind_rows(p4a_d1, p4a_d2, tibble(buffer=0,method="Equal-size control",R2=p4a_d1$R2[p4a_d1$buffer==0]))
p4a <- ggplot(p4a_dat, aes(buffer,R2,colour=method,shape=method)) +
  geom_line(linewidth=.85) + geom_point(size=2.7,fill="white",stroke=.9) +
  scale_colour_manual(values=c("Buffered"=red,"Equal-size control"=grey)) +
  scale_shape_manual(values=c("Buffered"=21,"Equal-size control"=24)) +
  scale_x_continuous(breaks=c(0,50,100,200)) + labs(x="Exclusion buffer (km)",y=expression(R[log]^2)) +
  theme(legend.position="bottom")

p4b_dat <- buff %>% filter(model=="RF",subset %in% depth_levels) %>% mutate(subset=factor(subset,depth_levels))
p4b <- ggplot(p4b_dat,aes(buffer_km,R2_mean,colour=subset,shape=subset)) +
  geom_errorbar(aes(ymin=R2_mean-R2_sd_offsets,ymax=R2_mean+R2_sd_offsets),width=4,linewidth=.4) +
  geom_line(linewidth=.8)+geom_point(size=2.5,fill="white",stroke=.8)+
  scale_colour_manual(values=depth_cols,labels=depth_labels)+scale_shape_manual(values=c(21,22,23,24),labels=depth_labels)+
  scale_x_continuous(breaks=c(0,50,100,200))+labs(x="Exclusion buffer (km)",y=expression(R[log]^2))+
  theme(legend.position="bottom")

p4c_dat <- ctrl %>% filter(buffer_km_target==200,subset %in% depth_levels) %>% mutate(subset=factor(subset,depth_levels))
p4c <- ggplot(p4c_dat,aes(subset,additional_buffer_penalty_mean,fill=subset))+
  geom_col(width=.66,colour="black",linewidth=.35)+
  geom_errorbar(aes(ymin=additional_buffer_penalty_q025,ymax=additional_buffer_penalty_q975),width=.16,linewidth=.5)+
  scale_fill_manual(values=depth_cols,guide="none")+scale_x_discrete(labels=depth_labels)+
  labs(x=NULL,y=expression("Additional "*Delta*R[log]^2*" loss at 200 km"))

fig4 <- (p4a | p4b | p4c) + plot_annotation(tag_levels="A")
save_figure(fig4,"Figure4_buffer_depth_dependence",183,82)

# ---------------- Figure 5: robustness and explanatory diagnostics ----------------
sens <- read_csv(file.path(data_dir,"depth_sensitivity_pooled_summary.csv"),show_col_types=FALSE) %>%
  filter(model=="RF",standard_depth %in% depth_levels) %>%
  mutate(standard_depth=factor(standard_depth,depth_levels),
         design=factor(design,levels=c("matched_n","matched_spatial","paired_profile"),
                       labels=c("Equal sample size","Equal spatial coverage","Paired profiles")))

p5a <- ggplot(sens,aes(standard_depth,R2_pooled_mean,colour=standard_depth))+
  geom_errorbar(aes(ymin=R2_pooled_q025,ymax=R2_pooled_q975),width=.14,linewidth=.45)+
  geom_point(size=2.5,shape=21,fill="white",stroke=.85)+
  facet_wrap(~design,nrow=1)+scale_colour_manual(values=depth_cols,guide="none")+
  scale_x_discrete(labels=depth_labels)+labs(x=NULL,y=expression(R[log]^2))+
  theme(axis.text.x=element_text(angle=35,hjust=1))

abl <- read_csv(file.path(data_dir,"bd_ablation_summary.csv"),show_col_types=FALSE) %>%
  filter(variant %in% c("full","no_bulk_density"),subset %in% c("all",depth_levels)) %>%
  mutate(subset=factor(subset,c("all",depth_levels),c("All","0–20 cm","20–50 cm","50–100 cm","100–200 cm")),
         variant=factor(variant,c("full","no_bulk_density"),c("Full model","Without bulk density")))
p5b <- ggplot(abl,aes(subset,R2_mean,colour=variant,group=variant,shape=variant))+
  geom_errorbar(aes(ymin=R2_mean-R2_sd,ymax=R2_mean+R2_sd),position=position_dodge(.22),width=.12,linewidth=.4)+
  geom_point(position=position_dodge(.22),size=2.4,fill="white",stroke=.8)+
  scale_colour_manual(values=c("Full model"="#356B8C","Without bulk density"=red))+
  scale_shape_manual(values=c("Full model"=21,"Without bulk density"=22))+
  labs(x=NULL,y=expression(R[log]^2))+theme(axis.text.x=element_text(angle=35,hjust=1),legend.position="bottom")

perm <- read_csv(file.path(data_dir,"grouped_permutation_summary.csv"),show_col_types=FALSE) %>%
  filter(subset=="all") %>%
  mutate(group=recode(group,bulk_density="Bulk density",layer_geometry="Layer geometry",climate="Climate",
                      soil_texture="Soil texture",soil_pH="Soil pH",topography="Topography",
                      vegetation_landcover="Vegetation / land cover")) %>%
  arrange(delta_R2_mean) %>% mutate(group=factor(group,levels=group))
p5c <- ggplot(perm,aes(delta_R2_mean,group))+
  geom_errorbarh(aes(xmin=delta_R2_q025,xmax=delta_R2_q975),height=.18,linewidth=.5,colour=grey)+
  geom_point(size=2.8,shape=21,fill="#78ABC5",stroke=.8)+geom_vline(xintercept=0,colour="grey80")+
  labs(x=expression(Delta*R[log]^2*" after grouped permutation"),y=NULL)

fig5 <- (p5a / (p5b | p5c)) + plot_layout(heights=c(1,1.08)) + plot_annotation(tag_levels="A")
save_figure(fig5,"Figure5_robustness_and_explanation",183,145)

message("Finished. Outputs: ", normalizePath(out_dir))
