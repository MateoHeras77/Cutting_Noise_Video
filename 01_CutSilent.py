from moviepy.editor import VideoFileClip, concatenate_videoclips
import numpy as np
import wave
import os
import time
from tqdm import tqdm
import glob

def print_device_info():
    """Print information about available computing devices"""
    try:
        from numba import cuda
        if cuda.is_available():
            device = cuda.get_current_device()
            print(f"\n{'='*50}")
            print("🟢 GPU MODE ACTIVE")
            print(f"GPU Device: {device.name}")
            print(f"Compute Capability: {device.compute_capability}")
            print(f"Maximum Threads per Block: {device.MAX_THREADS_PER_BLOCK}")
            print(f"{'='*50}\n")
            return True
        else:
            print(f"\n{'='*50}")
            print("🔴 GPU NOT AVAILABLE - Falling back to CPU mode")
            print("Make sure NVIDIA drivers and CUDA toolkit are installed")
            print(f"{'='*50}\n")
            return False
    except ImportError:
        print(f"\n{'='*50}")
        print("🔴 CUDA LIBRARIES NOT FOUND - Falling back to CPU mode")
        print("Install required packages with:")
        print("pip install numba cupy-cuda12x")
        print(f"{'='*50}\n")
        return False

def remove_silence(video_path, threshold=0.01, min_silence_duration=1):
    """
    Remove silent parts from a video file using GPU if available.
    
    Args:
        video_path: Path to input video file
        threshold: Volume threshold below which audio is considered silent
        min_silence_duration: Minimum duration of silence in seconds
    """
    try:
        # Check for GPU availability
        use_gpu = print_device_info()
        
        if use_gpu:
            try:
                from numba import cuda
                
                @cuda.jit
                def detect_silence_gpu(audio_data, threshold, is_silent):
                    """CUDA kernel for parallel silence detection"""
                    idx = cuda.grid(1)
                    if idx < audio_data.shape[0]:
                        is_silent[idx] = abs(audio_data[idx]) < threshold
            except ImportError:
                print("Failed to initialize CUDA functions - falling back to CPU")
                use_gpu = False

        print(f"⏳ Loading video {video_path}...")
        video = VideoFileClip(video_path)
        
        print("⏳ Extracting audio...")
        temp_audio = "temp_audio.wav"
        video.audio.write_audiofile(temp_audio, fps=44100, verbose=False, logger=None)
        
        print("⏳ Analyzing audio...")
        processing_start = time.time()
        
        with wave.open(temp_audio, 'rb') as wf:
            audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            if wf.getnchannels() == 2:
                audio_data = audio_data.reshape(-1, 2).mean(axis=1)
            
            audio_data = audio_data.astype(np.float32) / np.max(np.abs(audio_data))
            
            if use_gpu:
                print("🔄 Processing on GPU...")
                threadsperblock = 256
                blockspergrid = (audio_data.shape[0] + (threadsperblock - 1)) // threadsperblock
                
                d_audio = cuda.to_device(audio_data)
                d_is_silent = cuda.device_array(audio_data.shape[0], dtype=np.bool_)
                
                detect_silence_gpu[blockspergrid, threadsperblock](d_audio, threshold, d_is_silent)
                cuda.synchronize()
                
                is_silent = d_is_silent.copy_to_host()
            else:
                print("🔄 Processing on CPU...")
                is_silent = np.abs(audio_data) < threshold
            
        processing_time = time.time() - processing_start
        print(f"✨ Audio analysis completed in {processing_time:.2f} seconds using {'GPU' if use_gpu else 'CPU'}")
            
        # Group samples into windows
        window_size = int(44100 * min_silence_duration)
        num_windows = len(is_silent) // window_size
        
        keep_segments = []
        start_time = 0
        
        print("⏳ Processing segments...")
        for i in tqdm(range(num_windows)):
            window = is_silent[i * window_size:(i + 1) * window_size]
            if np.mean(window) < 0.8:  # If less than 80% of window is silent
                continue
            else:
                if start_time < (i * window_size / 44100):
                    keep_segments.append((
                        start_time,
                        i * window_size / 44100
                    ))
                start_time = (i + 1) * window_size / 44100
        
        if start_time < video.duration:
            keep_segments.append((start_time, video.duration))
        
        os.remove(temp_audio)
        
        print("⏳ Creating output video...")
        if keep_segments:
            clips = []
            for start, end in tqdm(keep_segments, desc="Processing video segments"):
                clips.append(video.subclip(start, end))
            
            final_video = concatenate_videoclips(clips)
            
            output_path = video_path.rsplit('.', 1)[0] + '_no_silence.mp4'
            print(f"💾 Saving to {output_path}...")
            
            # Try to use GPU encoding if available
            try:
                final_video.write_videofile(output_path, 
                                          audio_codec='aac',
                                          codec='h264_nvenc' if use_gpu else 'libx264',
                                          preset='fast',
                                          verbose=False,
                                          logger=None)
                print(f"✅ Video saved successfully using {'GPU' if use_gpu else 'CPU'} encoder!")
            except Exception as e:
                print(f"⚠️ GPU encoding failed, falling back to CPU: {str(e)}")
                final_video.write_videofile(output_path, 
                                          audio_codec='aac',
                                          codec='libx264',
                                          preset='fast',
                                          verbose=False,
                                          logger=None)
            
            final_video.close()
        
        video.close()
        print("✅ Processing completed!")
        
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        if os.path.exists("temp_audio.wav"):
            os.remove("temp_audio.wav")

if __name__ == "__main__":

    input_folder_path = r"C:\Users\wmate\OneDrive\Trabajo\UDEMY\Prueba\RawVideos"
    video_files = glob.glob(os.path.join(input_folder_path, "*.mp4"))
    
    for video_path in video_files:
        print(f"🔍 Processing file: {video_path}")
        remove_silence(video_path)
