package com.music.analytics;

import java.io.IOException;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.TextInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.TextOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

/**
 * Native Hadoop MapReduce Job for Artist Popularity and Catalog Aggregations.
 * Solves:
 *   - Total tracks per artist
 *   - Average popularity per artist
 *   - Minimum and Maximum popularity
 *   - Average track duration in seconds
 */
public class ArtistAnalyticsJob extends Configured implements Tool {

    public static class ArtistMapper extends Mapper<LongWritable, Text, Text, Text> {
        private final Text outKey = new Text();
        private final Text outValue = new Text();

        @Override
        protected void map(LongWritable key, Text value, Context context)
                throws IOException, InterruptedException {
            String line = value.toString().trim();
            if (line.isEmpty()) {
                return;
            }

            // Expected format: tab-separated fields:
            // 0: track_id, 1: track_name, 2: artist_name, 3: album_name,
            // 4: genre, 5: popularity, 6: duration_ms, 7: explicit, 8: year
            String[] tokens = line.split("\t");
            if (tokens.length >= 7) {
                String artist = tokens[2].trim();
                try {
                    int popularity = Integer.parseInt(tokens[5].trim());
                    long durationMs = Long.parseLong(tokens[6].trim());

                    if (!artist.isEmpty()) {
                        outKey.set(artist);
                        // value format: "popularity:durationMs"
                        outValue.set(popularity + ":" + durationMs);
                        context.write(outKey, outValue);
                    }
                } catch (NumberFormatException e) {
                    // Skip corrupt rows safely
                    context.getCounter("DataQuality", "MalformedNumericRows").increment(1);
                }
            } else {
                context.getCounter("DataQuality", "InsufficientTokensRows").increment(1);
            }
        }
    }

    public static class ArtistReducer extends Reducer<Text, Text, Text, Text> {
        private final Text outValue = new Text();

        @Override
        protected void reduce(Text key, Iterable<Text> values, Context context)
                throws IOException, InterruptedException {
            long count = 0;
            long totalPopularity = 0;
            long totalDurationMs = 0;
            int minPopularity = Integer.MAX_VALUE;
            int maxPopularity = Integer.MIN_VALUE;

            for (Text val : values) {
                String[] parts = val.toString().split(":");
                if (parts.length == 2) {
                    try {
                        int pop = Integer.parseInt(parts[0]);
                        long dur = Long.parseLong(parts[1]);

                        count++;
                        totalPopularity += pop;
                        totalDurationMs += dur;

                        if (pop < minPopularity) minPopularity = pop;
                        if (pop > maxPopularity) maxPopularity = pop;
                    } catch (NumberFormatException ignored) {}
                }
            }

            if (count > 0) {
                double avgPopularity = Math.round(((double) totalPopularity / count) * 100.0) / 100.0;
                double avgDurationSec = Math.round(((double) totalDurationMs / count / 1000.0) * 100.0) / 100.0;

                // Output format: count \t avg_popularity \t min_pop \t max_pop \t avg_duration_sec
                String result = String.format("%d\t%.2f\t%d\t%d\t%.2f",
                        count, avgPopularity, minPopularity, maxPopularity, avgDurationSec);
                outValue.set(result);
                context.write(key, outValue);
            }
        }
    }

    @Override
    public int run(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: ArtistAnalyticsJob <input_path> <output_path>");
            return -1;
        }

        Configuration conf = getConf();
        Job job = Job.getInstance(conf, "ArtistAnalyticsJob");
        job.setJarByClass(ArtistAnalyticsJob.class);

        job.setMapperClass(ArtistMapper.class);
        job.setReducerClass(ArtistReducer.class);

        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(Text.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        job.setInputFormatClass(TextInputFormat.class);
        job.setOutputFormatClass(TextOutputFormat.class);

        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));

        return job.waitForCompletion(true) ? 0 : 1;
    }

    public static void main(String[] args) throws Exception {
        int res = ToolRunner.run(new Configuration(), new ArtistAnalyticsJob(), args);
        System.exit(res);
    }
}
