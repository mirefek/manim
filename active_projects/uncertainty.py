from helpers import *
import scipy

from animation.animation import Animation
from animation.transform import *
from animation.simple_animations import *
from animation.playground import *
from animation.continual_animation import *
from topics.geometry import *
from topics.characters import *
from topics.functions import *
from topics.fractals import *
from topics.number_line import *
from topics.combinatorics import *
from topics.numerals import *
from topics.three_dimensions import *
from topics.objects import *
from topics.probability import *
from topics.complex_numbers import *
from topics.common_scenes import *
from scene import Scene
from scene.reconfigurable_scene import ReconfigurableScene
from scene.zoomed_scene import *
from camera import Camera
from mobject import *
from mobject.image_mobject import *
from mobject.vectorized_mobject import *
from mobject.svg_mobject import *
from mobject.tex_mobject import *
from topics.graph_scene import *

from active_projects.fourier import *


FREQUENCY_COLOR = RED
USE_ALMOST_FOURIER_BY_DEFAULT = False

class GaussianDistributionWrapper(Line):
    """
    This is meant to encode a 2d normal distribution as
    a mobject (so as to be able to have it be interpolated
    during animations).  It is a line whose start_point coordinates
    encode the coordinates of mu, and whose end_point - start_point
    encodes the coordinates of sigma.
    """
    CONFIG = {
        "stroke_width" : 0,
        "mu_x" : 0,
        "sigma_x" : 1,
        "mu_y" : 0,
        "sigma_y" : 0,
    }
    def __init__(self, **kwargs):
        Line.__init__(self, ORIGIN, RIGHT, **kwargs)
        self.change_parameters(self.mu_x, self.mu_y, self.sigma_x, self.sigma_y)

    def change_parameters(self, mu_x = None, mu_y = None, sigma_x = None, sigma_y = None):
        curr_parameters = self.get_parameteters()
        args = [mu_x, mu_y, sigma_x, sigma_y]
        new_parameters = [
            arg or curr
            for curr, arg in zip(curr_parameters, args)
        ]
        mu_x, mu_y, sigma_x, sigma_y = new_parameters
        mu_point = mu_x*RIGHT + mu_y*UP
        sigma_vect = sigma_x*RIGHT + sigma_y*UP
        self.put_start_and_end_on(mu_point, mu_point + sigma_vect)
        return self

    def get_parameteters(self):
        """ Return mu_x, mu_y, sigma_x, sigma_y"""
        start, end = self.get_start_and_end()
        return tuple(it.chain(start[:2], (end - start)[:2]))

    def get_random_points(self, size = 1):
        mu_x, mu_y, sigma_x, sigma_y = self.get_parameteters()
        x_vals = np.random.normal(mu_x, sigma_x, size)
        y_vals = np.random.normal(mu_y, sigma_y, size)
        return np.array([
            x*RIGHT + y*UP
            for x, y in zip(x_vals, y_vals)
        ])

class ProbabalisticMobjectCloud(ContinualAnimation):
    CONFIG = {
        "fill_opacity" : 0.25,
        "n_copies" : 100,
        "gaussian_distribution_wrapper_config" : {
            "sigma_x" : 1,
        }
    }
    def __init__(self, prototype, **kwargs):
        digest_config(self, kwargs)
        fill_opacity = self.fill_opacity or prototype.get_fill_opacity()
        self.gaussian_distribution_wrapper = GaussianDistributionWrapper(
            **self.gaussian_distribution_wrapper_config
        )
        group = VGroup(*[
            prototype.copy().set_fill(opacity = fill_opacity)
            for x in range(self.n_copies)
        ])
        ContinualAnimation.__init__(self, group, **kwargs)

    def update_mobject(self, dt):
        group = self.mobject
        points = self.gaussian_distribution_wrapper.get_random_points(len(group))
        for mob, point in zip(group, points):
            self.update_mobject_by_point(mob, point)
        return self

    def update_mobject_by_point(self, mobject, point):
        mobject.move_to(point)
        return self

class ProbabalisticDotCloud(ProbabalisticMobjectCloud):
    CONFIG = {
        "color" : BLUE,
    }
    def __init__(self, **kwargs):
        digest_config(self, kwargs)
        dot = Dot(color = self.color)
        ProbabalisticMobjectCloud.__init__(self, dot)

class ProbabalisticVectorCloud(ProbabalisticMobjectCloud):
    CONFIG = {
        "color" : RED,
        "n_copies" : 20,
        "fill_opacity" : 0.5,
        "center_func" : lambda : ORIGIN,
    }
    def __init__(self, **kwargs):
        digest_config(self, kwargs)
        vector = Vector(
            RIGHT, color = self.color,
            max_tip_length_to_length_ratio = 1,
        )
        ProbabalisticMobjectCloud.__init__(self, vector)

    def update_mobject_by_point(self, vector, point):
        vector.put_start_and_end_on(
            self.center_func(),
            point
        )

###################

class MentionUncertaintyPrinciple(TeacherStudentsScene):
    def construct(self):
        title = TextMobject("Heisenberg Uncertainty Principle")
        title.to_edge(UP)

        dot_cloud = ProbabalisticDotCloud()
        vector_cloud = ProbabalisticVectorCloud(
            gaussian_distribution_wrapper_config = {"sigma_x" : 0.2},
            center_func = dot_cloud.gaussian_distribution_wrapper.get_start,
        )
        for cloud in dot_cloud, vector_cloud:
            gdw = cloud.gaussian_distribution_wrapper
            gdw.move_to(title.get_center(), LEFT)
            gdw.shift(2*DOWN)
        vector_cloud.gaussian_distribution_wrapper.shift(3*RIGHT)

        def get_brace_text_group_update(gdw, vect, text):
            brace = Brace(gdw, vect)
            text = brace.get_tex("\\sigma_{\\text{%s}}"%text, buff = SMALL_BUFF)
            group = VGroup(brace, text)
            def update_group(group):
                brace, text = group
                brace.match_width(gdw, stretch = True)
                brace.next_to(gdw, vect)
                text.next_to(brace, vect, buff = SMALL_BUFF)
            return ContinualUpdateFromFunc(group, update_group)

        dot_brace_anim = get_brace_text_group_update(
            dot_cloud.gaussian_distribution_wrapper,
            DOWN, "position",
        )
        vector_brace_anim = get_brace_text_group_update(
            vector_cloud.gaussian_distribution_wrapper,
            UP, "momentum",
        )

        self.add(title)
        self.add(dot_cloud)
        self.play(
            Write(title),
            self.teacher.change, "raise_right_hand",
            self.get_student_changes(*["pondering"]*3)
        )
        self.play(
            Write(dot_brace_anim.mobject, run_time = 1)
        )
        self.add(dot_brace_anim)
        self.wait()
        # self.wait(2)
        self.play(
            dot_cloud.gaussian_distribution_wrapper.change_parameters, 
            {"sigma_x" : 0.1},
            run_time = 2,
        )
        self.wait()
        self.add(vector_cloud)
        self.play(
            FadeIn(vector_brace_anim.mobject)
        )
        self.add(vector_brace_anim)
        self.play(
            vector_cloud.gaussian_distribution_wrapper.change_parameters,
            {"sigma_x" : 1},
            self.get_student_changes(*3*["confused"]),
            run_time = 3,
        )
        #Back and forth
        for x in range(2):
            self.play(
                dot_cloud.gaussian_distribution_wrapper.change_parameters,
                {"sigma_x" : 2},
                vector_cloud.gaussian_distribution_wrapper.change_parameters,
                {"sigma_x" : 0.1},
                run_time = 3,
            )
            self.change_student_modes("thinking", "erm", "sassy")
            self.play(
                dot_cloud.gaussian_distribution_wrapper.change_parameters,
                {"sigma_x" : 0.1},
                vector_cloud.gaussian_distribution_wrapper.change_parameters,
                {"sigma_x" : 1},
                run_time = 3,
            )
            self.wait()

class FourierTradeoff(Scene):
    def construct(self):
        #Setup axes
        time_mean = 4
        time_axes = Axes(
            x_min = 0,
            x_max = 2*time_mean,
            x_axis_config = {"unit_size" : 1.5},
            y_min = -2, 
            y_max = 2,
            y_axis_config = {"unit_size" : 0.5}
        )
        time_label = TextMobject("Time")
        time_label.next_to(
            time_axes.x_axis.get_right(), UP,
            buff = MED_SMALL_BUFF,
        )
        time_axes.add(time_label)
        time_axes.center().to_edge(UP)
        time_axes.x_axis.add_numbers(*range(1, 2*time_mean))

        frequency_axes = Axes(
            x_min = 0,
            x_max = 8,
            x_axis_config = {"unit_size" : 1.5},
            y_min = 0,
            y_max = 15,
            y_axis_config = {
                "unit_size" : 0.15,
                "tick_frequency" : 5,
            },
            color = TEAL,
        )
        frequency_label = TextMobject("Frequency")
        frequency_label.next_to(
            frequency_axes.x_axis.get_right(), UP,
            buff = MED_SMALL_BUFF, 
        )
        frequency_label.highlight(FREQUENCY_COLOR)
        frequency_axes.add(frequency_label)
        frequency_axes.move_to(time_axes, LEFT)
        frequency_axes.to_edge(DOWN, buff = LARGE_BUFF)
        frequency_axes.x_axis.add_numbers()

        # Graph information

        #x-coordinate of this point determines width of wave_packet graph
        width_tracker = VectorizedPoint(0.5*RIGHT)
        def get_width():
            return width_tracker.get_center()[0]

        def get_wave_packet_function():
            factor = 1./get_width()
            return lambda t : np.sqrt(factor)*np.cos(4*TAU*t)*np.exp(-factor*(t-time_mean)**2)

        def get_wave_packet():
            graph = time_axes.get_graph(
                get_wave_packet_function(),
                num_graph_points = 200,
            )
            graph.highlight(YELLOW)
            return graph

        time_radius = 10
        def get_wave_packet_fourier_transform():
            return get_fourier_graph(
                frequency_axes, get_wave_packet_function(),
                t_min = time_mean - time_radius,
                t_max = time_mean + time_radius,
                n_samples = 2*time_radius*17,
                complex_to_real_func = abs,
                color = FREQUENCY_COLOR,
            )

        wave_packet = get_wave_packet()
        wave_packet_update = UpdateFromFunc(
            wave_packet, 
            lambda g : Transform(g, get_wave_packet()).update(1)
        )
        fourier_graph = get_wave_packet_fourier_transform()
        fourier_graph_update = UpdateFromFunc(
            fourier_graph, 
            lambda g : Transform(g, get_wave_packet_fourier_transform()).update(1)
        )

        arrow = Arrow(
            wave_packet, frequency_axes.coords_to_point(4, 10),
            color = FREQUENCY_COLOR,
        )
        fourier_words = TextMobject("Fourier Transform")
        fourier_words.next_to(arrow, RIGHT, buff = MED_LARGE_BUFF)
        sub_words = TextMobject("(To be explained shortly)")
        sub_words.highlight(BLUE)
        sub_words.scale(0.75)
        sub_words.next_to(fourier_words, DOWN)

        #Draw items
        self.add(time_axes, frequency_axes)
        self.play(ShowCreation(wave_packet))
        self.play(
            ReplacementTransform(
                wave_packet.copy(),
                fourier_graph,
            ),
            GrowArrow(arrow),
            Write(fourier_words, run_time = 1)
        )
        # self.play(FadeOut(arrow))
        self.wait()
        for width in 6, 0.1, 1:
            self.play(
                width_tracker.move_to, width*RIGHT,
                wave_packet_update,
                fourier_graph_update,
                run_time = 3
            )
            if sub_words not in self.mobjects:
                self.play(FadeIn(sub_words))
            else:
                self.wait()
        self.wait()







































