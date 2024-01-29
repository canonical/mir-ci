import asyncio
import base64
import os
import time

from io import BytesIO
from typing import List

import cv2
import numpy as np

from moviepy.editor import ImageClip, concatenate_videoclips
from PIL import Image
from RPA.Images import Images
from RPA.recognition.templates import ImageNotFoundError
# from RPA.core.geometry import Region

from mir_ci.screencopy_tracker import ScreencopyTracker
from robot.api import logger
from robot.api.deco import keyword, library



@library(scope="GLOBAL")
class Screencopy(ScreencopyTracker):

    ROBOT_LISTENER_API_VERSION = 3
    TOLERANCE = 0.8

    def __init__(self) -> None:
        self.ROBOT_LIBRARY_LISTENER = self
        display_name = os.environ.get("WAYLAND_DISPLAY", "wayland-0")
        super().__init__(display_name)
        self._rpa_images = Images()
        self.frames = []

    @keyword
    async def save_frame(self):
        await self.connect()
        screenshot = self.grab_screenshot()
        screenshot.save(f"frame_{self.frame_count}.png")

    # @keyword
    # async def record_as_gif(self, file_path : str, duration : float, fps : float = 24):
    #     """
    #     Record the screen for the given duration and save the recording to an animated GIF file.

    #     :param file_path: path to the output GIF file
    #     :param duration: duration in seconds
    #     :param fps: frames per second
    #     """
    #     await self.connect()

    #     frames = []
    #     last_frame_count = 0
    #     start_time = time.time()
    #     current_time = start_time
    #     time_next_frame = start_time
    #     end_time = start_time + duration
    #     while current_time < end_time:
    #         if self.frame_count != last_frame_count:
    #             last_frame_count = self.frame_count
    #             if current_time >= time_next_frame:
    #                 time_diff = time_next_frame - current_time
    #                 time_next_frame = current_time - time_diff + 1.0 / fps
    #                 frames.append((self.grab_screenshot(), time_next_frame))
    #         else:
    #             await asyncio.sleep(0)
    #         current_time = time.time()

    #     if len(frames) > 0:
    #         # logger.info(f"Frames: {len(frames)}")
    #         frame_durations = []
    #         for index in range(len(frames) - 1):
    #             current_frame_time, next_frame_time = (frames[index][1], frames[index + 1][1])
    #             frame_duration = next_frame_time - current_frame_time
    #             frame_durations.append(frame_duration)
    #         frame_durations.append(float(duration - sum(frame_durations)))

    #         images = [frame[0] for frame in frames]
    #         images[0].save(
    #             file_path,
    #             save_all = True,
    #             append_images = images[1:],
    #             loop = 0,
    #             duration = [duration * 1000 for duration in frame_durations]
    #         )

    # Fixed time between frames:

    # @keyword
    # async def record_as_video(self, file_path : str, duration : float, fps : float = 24):
    #     """
    #     Record the screen for the given duration and save the recording to a video file.

    #     :param file_path: path to the output video file
    #     :param duration: duration in seconds
    #     :param fps: frames per second
    #     """
    #     await self.connect()

    #     frames = []
    #     last_frame_count = 0
    #     start_time = time.time()
    #     current_time = start_time
    #     time_next_frame = start_time
    #     end_time = start_time + duration
    #     while current_time < end_time:
    #         if self.frame_count != last_frame_count:
    #             last_frame_count = self.frame_count
    #             if current_time >= time_next_frame:
    #                 time_diff = time_next_frame - current_time
    #                 time_next_frame = current_time - time_diff + 1.0 / fps
    #                 frames.append(self.grab_screenshot())
    #         else:
    #             await asyncio.sleep(0)
    #         current_time = time.time()

    #     if len(frames) > 0:
    #         fps = len(frames) / duration
    #         width, height = frames[0].size

    #         logger.info(f"Frames: {len(frames)}")
    #         logger.info(f"FPS: {fps}   Size: {width, height}")

    #         fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #         video = cv2.VideoWriter(file_path, fourcc, fps, (width, height))
    #         for frame in frames:
    #             frame_np = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
    #             video.write(frame_np)
    #         video.release()

    # Varying time between frames:

    @keyword
    async def record_as_video(self, file_path : str, duration : float, fps : float = 5):
        """
        Record the screen for the given duration and save the recording to a video file.

        :param file_path: path to the output video file
        :param duration: duration in seconds
        :param fps: frames per second
        """
        await self.connect()

        frames = []
        last_frame_count = 0
        start_time = time.time()
        current_time = start_time
        time_next_frame = start_time
        end_time = start_time + duration
        while current_time < end_time:
            if self.frame_count != last_frame_count:
                last_frame_count = self.frame_count
                if current_time >= time_next_frame:
                    time_diff = time_next_frame - current_time
                    time_next_frame = current_time - time_diff + 1.0 / fps
                    frames.append((self.grab_screenshot(), time_next_frame))
            else:
                await asyncio.sleep(0)
            current_time = time.time()

        if len(frames) > 0:
            frame_durations = []
            for index in range(len(frames) - 1):
                current_frame_time, next_frame_time = (frames[index][1], frames[index + 1][1])
                frame_duration = next_frame_time - current_frame_time
                frame_durations.append(frame_duration)
            frame_durations.append(float(duration - sum(frame_durations)))

            frame_clips = [ImageClip(np.array(frame[0])) for frame in frames]
            # frame_clips = [ImageClip(cv2.cvtColor(np.array(frame[0]), cv2.COLOR_RGB2BGR)) for frame in frames]

            clips_with_durations = [clip.set_duration(duration) for clip, duration in zip(frame_clips, frame_durations)]
            final_clip = concatenate_videoclips(clips_with_durations)
            final_clip.write_videofile(file_path, fps=fps, codec="png")

    # @keyword
    # async def save_frames(self):
    #     await self.connect()
    #     last_frame = 0
    #     end_time = time.time() + duration
    #     while time.time() < end_time:
    #         if self.frame_count != last_frame:
    #             last_frame = self.frame_count
    #             screenshot = self.grab_screenshot()
    #             # logger.info(f"frame_{self.frame_count}.png")
    #             screenshot.save(f"frame_{self.frame_count}.png")
    #         else:
    #             await asyncio.sleep(0)
            
    # @keyword
    # async def start_recording(self):
    #     self.frames = []
    #     self.recording = True

    # @keyword
    # async def stop_recording(self):
    #     self.recording = False

    @keyword
    async def test_match(self, template: str):
        """
        Grab a screenshot and check for a match with the given template.

        :param template: path to an image file to be used as template
        """
        await self.connect()
        try:
            screenshot = self.grab_screenshot()
            self._rpa_images.find_template_in_image(
                screenshot,
                template,
                tolerance=self.TOLERANCE,
            )
        except (RuntimeError, ValueError, ImageNotFoundError) as exc:
            self._log_failed_match(screenshot, template)
            raise ImageNotFoundError from exc

    @keyword
    async def wait_match(self, template: str, timeout: int = 10) -> List[dict]:
        """
        Grab screenshots and compare until there's a match with the provided
        template.

        :param template: path to an image file to be used as template
        :param timeout: timeout in seconds
        """
        await self.connect()
        regions = []
        last_frame_count = 0
        matched = False
        screenshot = None
        end_time = time.time() + float(timeout)
        while time.time() < end_time:
            if self.frame_count == last_frame_count:
                await asyncio.sleep(0)
            else:
                last_frame_count = self.frame_count
                try:
                    screenshot = self.grab_screenshot()
                    regions = self._rpa_images.find_template_in_image(
                        screenshot,
                        template,
                        tolerance=self.TOLERANCE,
                    )
                    matched = True
                    # for region in regions:
                    #     logger.info("Region: " + str(region.as_tuple))
                    break
                except (RuntimeError, ValueError, ImageNotFoundError):
                    continue

        if not matched:
            self._log_failed_match(screenshot, template)
            raise ImageNotFoundError

        return [
            {
                "left": region.left,
                "top": region.top,
                "right": region.right,
                "bottom": region.bottom
            }
            for region in regions
        ]

    def grab_screenshot(self) -> Image.Image:
        """Grab a screenshot from the latest captured frame."""
        assert self.shm_data is not None, "No SHM data available"

        self.shm_data.seek(0)
        data = self.shm_data.read()
        size = (self.buffer_width, self.buffer_height)
        stride = self.buffer_stride
        image = Image.frombytes("RGBA", size, data, "raw", "RGBA", stride, -1)
        b, g, r, a, *_ = image.split()
        image = Image.merge("RGBA", (r, g, b, a))

        return image

    async def connect(self):
        """Connect to the display."""
        if not self.shm_data:
            await super().connect()
            # Wait for the first frame to become ready
            while self.frame_count == 0:
                await asyncio.sleep(0)

    async def disconnect(self):
        """Disconnect from the display."""
        if self.shm_data:
            await super().disconnect()

    def _close(self):
        """Listener method called when the library goes out of scope."""
        asyncio.get_event_loop().run_until_complete(self.disconnect())

    @staticmethod
    def _to_base64(image: Image.Image) -> str:
        """Convert Pillow Image to b64"""
        im_file = BytesIO()
        image.save(im_file, format="PNG")
        im_bytes = im_file.getvalue()
        im_b64 = base64.b64encode(im_bytes)
        return im_b64.decode()

    def _log_failed_match(self, screenshot, template):
        """Log a failure with template matching."""
        if not screenshot:
            return

        template_img = Image.open(template)
        template_string = (
            'Template was:<br><img src="data:image/png;base64,'
            f'{self._to_base64(template_img)}" /><br>'
        )
        image_string = (
            'Image was:<br><img src="data:image/png;base64,'
            f'{self._to_base64(screenshot)}" />'
        )
        logger.info(
            template_string + image_string,
            html=True,
        )
