@echo off
REM Downloads Wan 2.2 image-to-video (14B fp8) + 4-step LoRAs into your ComfyUI models folder. Resumes if interrupted.
REM Usage:  get_wan22.bat "C:\path\to\ComfyUI"
set COMFY=%~1
if "%COMFY%"=="" ( echo Usage: get_wan22.bat "C:\path\to\ComfyUI"  & exit /b 1 )
set M=%COMFY%\models
set HF=https://huggingface.co/Comfy-Org/Wan-2.2/resolve/main/split_files
mkdir "%M%\diffusion_models" "%M%\text_encoders" "%M%\vae" "%M%\loras" 2>nul
curl -L -C - -o "%M%\vae\wan_2.1_vae.safetensors" %HF%/vae/wan_2.1_vae.safetensors
curl -L -C - -o "%M%\loras\wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors" %HF%/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors
curl -L -C - -o "%M%\loras\wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors" %HF%/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors
curl -L -C - -o "%M%\text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors" %HF%/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
curl -L -C - -o "%M%\diffusion_models\wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" %HF%/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
curl -L -C - -o "%M%\diffusion_models\wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" %HF%/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
echo.
echo Done. Restart ComfyUI so it sees the new models.
